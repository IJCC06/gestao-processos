from flask import Blueprint, render_template, request
from flask_login import login_required, current_user

from processos.models import Auditoria

auditoria_bp = Blueprint("auditoria", __name__, url_prefix="/admin/auditoria")


@auditoria_bp.get("/")
@login_required
def list():
    if not current_user.is_admin:
        from flask import abort
        abort(403)

    pagina = max(request.args.get("page", 1, type=int), 1)
    por_pagina = 50
    consulta = Auditoria.query.order_by(Auditoria.criado_em.desc())
    total = consulta.count()
    registros = (
        consulta.offset((pagina - 1) * por_pagina)
        .limit(por_pagina)
        .all()
    )
    total_paginas = max((total + por_pagina - 1) // por_pagina, 1)

    return render_template(
        "admin/auditoria.html",
        auditorias=registros,
        pagina=pagina,
        total_paginas=total_paginas,
        total=total,
    )
