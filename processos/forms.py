from django import forms

from .models import Cliente


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
