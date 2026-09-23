from django import forms

from .models import Cliente, Processo


class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ["nome", "cpf_cnpj", "contato", "endereco", "observacoes"]
        widgets = {
            "nome": forms.TextInput(attrs={"placeholder": "Nome completo ou razão social"}),
            "cpf_cnpj": forms.TextInput(attrs={"placeholder": "CPF ou CNPJ"}),
            "contato": forms.TextInput(attrs={"placeholder": "Telefone ou e-mail"}),
            "endereco": forms.TextInput(attrs={"placeholder": "Endereço"}),
            "observacoes": forms.Textarea(attrs={"rows": 5, "placeholder": "Observações"}),
        }

    def clean_nome(self):
        nome = self.cleaned_data["nome"].strip()
        if not nome:
            raise forms.ValidationError("Informe o nome do cliente.")
        return nome

    def clean_cpf_cnpj(self):
        valor = self.cleaned_data["cpf_cnpj"].strip()
        if not valor:
            raise forms.ValidationError("Informe o CPF ou CNPJ.")
        return valor


class ProcessoForm(forms.ModelForm):
    class Meta:
        model = Processo
        fields = ["cliente", "numero_cnj", "area", "tribunal", "tribunal_alias", "fase", "status", "valor_causa", "honorarios"]
        widgets = {
            "numero_cnj": forms.TextInput(attrs={"placeholder": "Número CNJ"}),
            "tribunal": forms.TextInput(attrs={"placeholder": "Tribunal ou vara"}),
            "tribunal_alias": forms.TextInput(attrs={"placeholder": "Ex.: trt2, tjsp, trf3"}),
            "fase": forms.TextInput(attrs={"placeholder": "Fase processual"}),
            "valor_causa": forms.NumberInput(attrs={"step": "0.01"}),
            "honorarios": forms.NumberInput(attrs={"step": "0.01"}),
        }

    def clean_numero_cnj(self):
        valor = self.cleaned_data["numero_cnj"].strip()
        if not valor:
            raise forms.ValidationError("Informe o número do processo.")
        return valor
