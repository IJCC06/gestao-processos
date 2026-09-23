import os
from datetime import timedelta
from functools import wraps

from dotenv import load_dotenv
from flask import Flask, abort, flash, g, redirect, render_template, request, session, url_for
from flask_login import LoginManager, current_user, login_required, login_user, logout_user
from flask_wtf import CSRFProtect

from config.settings import Config
from processos.extensions import db
from processos.models import Cliente, Movimentacao, Prazo, Processo, Usuario
from processos.services.movimentacoes import verificar_movimentacoes

load_dotenv()

login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.login_message = "Entre com sua conta para acessar o sistema."
csrf = CSRFProtect()


def create_app():
    app = Flask(__name__, template_folder="processos/templates", static_folder="processos/static")
    app.config.from_object(Config)
    if os.environ.get("DATABASE_URL"):
        app.config["SQLALCHEMY_DATABASE_URI"] = os.environ["DATABASE_URL"]
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    with app.app_context():
        db.create_all()

    register_routes(app)
    register_cli(app)
    return app


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(Usuario, int(user_id))


def register_routes(app):
    @app.context_processor
    def inject_helpers():
        return {"current_user": current_user}

    @app.route("/login/", methods=["GET", "POST"])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for("dashboard"))
        if request.method == "POST":
            usuario = Usuario.query.filter_by(username=request.form.get("username", "").strip()).first()
            if usuario and usuario.check_password(request.form.get("password", "")):
                login_user(usuario)

                # Consulta o DataJud uma vez a cada login, sem Celery/Redis.
                resultado = verificar_movimentacoes()
                if resultado["erros"]:
                    flash(
                        f"Consulta de movimentações concluída com {resultado['erros']} ocorrência(s) de erro ou configuração ausente.",
                        "warning",
                    )
                elif resultado["total_processos"]:
                    flash(
                        f"Consulta concluída: {resultado['total_novas']} movimentação(ões) nova(s) encontrada(s) em {resultado['total_processos']} processo(s).",
                        "success",
                    )

                return redirect(request.args.get("next") or url_for("dashboard"))
            flash("Usuário ou senha inválidos.", "error")
        return render_template("registration/login.html")

    @app.post("/logout/")
    @login_required
    def logout():
        logout_user()
        return redirect(url_for("login"))

    @app.get("/")
    @login_required
    def dashboard():
        hoje = Config.local_date()
        prazos = Prazo.query.filter_by(status=Prazo.Status.PENDENTE).all()
        prazos_vencidos = sorted([p for p in prazos if p.data_vencimento < hoje], key=lambda p: (p.data_vencimento, p.titulo))
        prazos_proximos = sorted([p for p in prazos if hoje <= p.data_vencimento <= hoje + timedelta(days=7)], key=lambda p: (p.data_vencimento, p.titulo))
        return render_template("processos/dashboard.html", total_clientes=Cliente.query.count(), total_processos=Processo.query.count(), processos_ativos=Processo.query.filter_by(status=Processo.Status.ATIVO).count(), alertas_pendentes=Processo.query.filter_by(alerta_pendente=True).count(), prazos_vencidos=prazos_vencidos, prazos_proximos=prazos_proximos, ultimas_movimentacoes=Movimentacao.query.order_by(Movimentacao.data.desc()).limit(10).all())

    @app.get("/clientes/")
    @login_required
    def cliente_list():
        busca=request.args.get("q", "").strip()
        clientes=Cliente.query.order_by(Cliente.nome).all()
        if busca:
            termo=busca.lower()
            clientes=[c for c in clientes if termo in c.nome.lower() or termo in c.cpf_cnpj.lower() or termo in (c.contato or "").lower()]
        return render_template("processos/clientes/list.html", clientes=clientes, busca=busca)

    @app.route("/clientes/novo/", methods=["GET","POST"])
    @login_required
    def cliente_create():
        return cliente_form()

    @app.route("/clientes/<int:pk>/editar/", methods=["GET","POST"])
    @login_required
    def cliente_update(pk):
        cliente=Cliente.query.get_or_404(pk)
        return cliente_form(cliente)

    def cliente_form(cliente=None):
        if request.method=="POST":
            nome=request.form.get("nome","").strip(); cpf=request.form.get("cpf_cnpj","").strip()
            if not nome or not cpf:
                flash("Informe o nome e o CPF/CNPJ.","error")
            elif Cliente.query.filter(Cliente.cpf_cnpj==cpf, Cliente.id != (cliente.id if cliente else 0)).first():
                flash("Já existe um cliente com este CPF/CNPJ.","error")
            else:
                if cliente is None: cliente=Cliente()
                cliente.nome=nome; cliente.cpf_cnpj=cpf; cliente.contato=request.form.get("contato","").strip(); cliente.endereco=request.form.get("endereco","").strip(); cliente.observacoes=request.form.get("observacoes","").strip()
                db.session.add(cliente); db.session.commit(); flash("Cliente salvo com sucesso.","success")
                return redirect(url_for("cliente_detail",pk=cliente.id))
        return render_template("processos/clientes/form.html", titulo="Editar cliente" if cliente else "Novo cliente", cliente=cliente)

    @app.get("/clientes/<int:pk>/")
    @login_required
    def cliente_detail(pk):
        return render_template("processos/clientes/detail.html", cliente=Cliente.query.get_or_404(pk))

    @app.route("/clientes/<int:pk>/excluir/", methods=["GET","POST"])
    @login_required
    def cliente_delete(pk):
        cliente=Cliente.query.get_or_404(pk)
        if request.method=="POST":
            if cliente.processos:
                flash("Não foi possível excluir este cliente. Existem processos vinculados.","error")
                return redirect(url_for("cliente_detail",pk=pk))
            db.session.delete(cliente); db.session.commit(); flash("Cliente excluído com sucesso.","success"); return redirect(url_for("cliente_list"))
        return render_template("processos/clientes/delete.html",cliente=cliente)

    @app.get("/processos/")
    @login_required
    def processo_list():
        busca=request.args.get("q","").strip(); status=request.args.get("status","").strip(); area=request.args.get("area","").strip()
        processos=Processo.query.all()
        if busca:
            t=busca.lower(); processos=[p for p in processos if t in p.numero_cnj.lower() or t in p.cliente.nome.lower() or t in (p.tribunal or "").lower()]
        if status in Processo.Status.values(): processos=[p for p in processos if p.status==status]
        if area in Processo.Area.values(): processos=[p for p in processos if p.area==area]
        return render_template("processos/processos/list.html",processos=processos,busca=busca,status=status,area=area,status_choices=Processo.Status.choices(),area_choices=Processo.Area.choices())

    @app.route("/processos/novo/",methods=["GET","POST"])
    @login_required
    def processo_create(): return processo_form()

    @app.route("/processos/<int:pk>/editar/",methods=["GET","POST"])
    @login_required
    def processo_update(pk): return processo_form(Processo.query.get_or_404(pk))

    def processo_form(processo=None):
        clientes=Cliente.query.order_by(Cliente.nome).all()
        if request.method=="POST":
            cliente=Cliente.query.get(request.form.get("cliente", type=int)); numero=request.form.get("numero_cnj","").strip()
            if not cliente or not numero: flash("Informe o cliente e o número do processo.","error")
            elif Processo.query.filter(Processo.numero_cnj==numero, Processo.id != (processo.id if processo else 0)).first(): flash("Já existe um processo com este número CNJ.","error")
            else:
                if processo is None: processo=Processo()
                processo.cliente=cliente; processo.numero_cnj=numero; processo.area=request.form.get("area",""); processo.tribunal=request.form.get("tribunal","").strip(); processo.tribunal_alias=request.form.get("tribunal_alias","").strip(); processo.fase=request.form.get("fase","").strip(); processo.status=request.form.get("status",Processo.Status.ATIVO); processo.valor_causa=request.form.get("valor_causa") or None; processo.honorarios=request.form.get("honorarios") or None
                db.session.add(processo); db.session.commit(); flash("Processo salvo com sucesso.","success"); return redirect(url_for("processo_detail",pk=processo.id))
        return render_template("processos/processos/form.html",titulo="Editar processo" if processo else "Novo processo",processo=processo,clientes=clientes)

    @app.get("/processos/<int:pk>/")
    @login_required
    def processo_detail(pk): return render_template("processos/processos/detail.html",processo=Processo.query.get_or_404(pk))

    @app.route("/prazos/novo/",methods=["GET","POST"])
    @login_required
    def prazo_create(): return prazo_form()

    @app.route("/prazos/<int:pk>/editar/",methods=["GET","POST"])
    @login_required
    def prazo_update(pk): return prazo_form(Prazo.query.get_or_404(pk))

    def prazo_form(prazo=None):
        processo_id=request.args.get("processo",type=int) if prazo is None else None
        processos=Processo.query.order_by(Processo.numero_cnj).all()
        if request.method=="POST":
            processo=Processo.query.get(request.form.get("processo",type=int)); titulo=request.form.get("titulo","").strip(); inicio=request.form.get("data_inicio") or None; venc=request.form.get("data_vencimento") or ""
            if not processo or not titulo or not venc: flash("Informe processo, título e vencimento.","error")
            elif inicio and venc < inicio: flash("A data de vencimento não pode ser anterior à data de início.","error")
            else:
                from datetime import date
                if prazo is None: prazo=Prazo()
                prazo.processo=processo; prazo.titulo=titulo; prazo.data_inicio=date.fromisoformat(inicio) if inicio else None; prazo.data_vencimento=date.fromisoformat(venc); prazo.status=request.form.get("status",Prazo.Status.PENDENTE); prazo.observacoes=request.form.get("observacoes","").strip()
                db.session.add(prazo); db.session.commit(); flash("Prazo salvo com sucesso.","success"); return redirect(url_for("prazo_detail",pk=prazo.id))
        return render_template("processos/prazos/form.html",titulo="Editar prazo" if prazo else "Novo prazo",prazo=prazo,processos=processos,processo_id=processo_id)

    @app.get("/prazos/")
    @login_required
    def prazo_list():
        status=request.args.get("status","").strip(); prazos=Prazo.query.order_by(Prazo.data_vencimento,Prazo.titulo).all()
        if status in Prazo.Status.values(): prazos=[p for p in prazos if p.status==status]
        return render_template("processos/prazos/list.html",prazos=prazos,status=status,status_choices=Prazo.Status.choices())

    @app.get("/prazos/<int:pk>/")
    @login_required
    def prazo_detail(pk): return render_template("processos/prazos/detail.html",prazo=Prazo.query.get_or_404(pk))

    @app.post("/prazos/<int:pk>/concluir/")
    @login_required
    def prazo_concluir(pk):
        prazo=Prazo.query.get_or_404(pk); prazo.status=Prazo.Status.CONCLUIDO; db.session.commit(); flash("Prazo marcado como concluído.","success"); return redirect(url_for("prazo_list"))

    @app.get("/notificacoes/")
    @login_required
    def notificacoes():
        hoje=Config.local_date(); prazos=Prazo.query.filter_by(status=Prazo.Status.PENDENTE).all()
        vencidos=[p for p in prazos if p.data_vencimento<hoje]; proximos=[p for p in prazos if hoje<=p.data_vencimento<=hoje+timedelta(days=7)]
        movimentos=Movimentacao.query.join(Processo).filter(Processo.alerta_pendente.is_(True)).order_by(Movimentacao.data.desc()).all()
        return render_template("processos/notificacoes.html",vencidos=vencidos,prazos_proximos=proximos,movimentos=movimentos)

    @app.post("/notificacoes/processos/<int:pk>/limpar/")
    @login_required
    def limpar_alerta_processo(pk):
        processo=Processo.query.get_or_404(pk); processo.alerta_pendente=False; db.session.commit(); flash("Alerta de movimentação marcado como visto.","success"); return redirect(url_for("notificacoes"))


def register_cli(app):
    @app.cli.command("verificar-movimentacoes")
    def verificar_movimentacoes_cli():
        resultado=verificar_movimentacoes()
        print(f"Verificação concluída: {resultado['total_processos']} processo(s) checado(s), {resultado['total_novas']} movimentação(ões) nova(s), {resultado['erros']} ocorrência(s) com erro ou configuração ausente.")


app=create_app()

if __name__=="__main__":
    app.run(debug=app.config["DEBUG"])
