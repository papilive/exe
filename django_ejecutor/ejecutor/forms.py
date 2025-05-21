"""
Forms for the ejecutor app.
"""
from django import forms
from .models import ExecutableFile, ExecutableCategory
import os

class ExecutableFileUploadForm(forms.ModelForm):
    """Form for uploading executable files."""
    class Meta:
        model = ExecutableFile
        fields = ['name', 'description', 'file', 'category', 'command_args']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = ExecutableCategory.objects.all()
        self.fields['category'].empty_label = "-- Seleccione una categoría --"

    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            # Check file extension
            ext = os.path.splitext(file.name)[1].lower()
            if ext != '.exe':
                raise forms.ValidationError("Solo se permiten archivos .exe")

            # Check file size (limit to 100MB)
            if file.size > 100 * 1024 * 1024:
                raise forms.ValidationError("El archivo no puede superar los 100MB")
        else:
            raise forms.ValidationError("Debe seleccionar un archivo")
        return file

class PreinstalledExecutableForm(forms.ModelForm):
    """Form for registering preinstalled executable files."""
    class Meta:
        model = ExecutableFile
        fields = ['name', 'description', 'file_path', 'category', 'command_args']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = ExecutableCategory.objects.all()
        self.fields['category'].empty_label = "-- Seleccione una categoría --"

    def clean_file_path(self):
        file_path = self.cleaned_data.get('file_path')
        if not file_path:
            raise forms.ValidationError("Debe especificar la ruta del archivo")
        return file_path

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.type = 'preinstalled'
        if commit:
            instance.save()
        return instance

class ExecutableSelectionForm(forms.Form):
    """Form for selecting an executable file to run."""
    executable = forms.ModelChoiceField(
        queryset=ExecutableFile.objects.filter(is_active=True),
        empty_label="-- Seleccione un ejecutable --",
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Ejecutable"
    )

    def __init__(self, *args, category=None, **kwargs):
        super().__init__(*args, **kwargs)
        if category:
            self.fields['executable'].queryset = ExecutableFile.objects.filter(
                is_active=True, category=category
            )

class ExecutableArgumentsForm(forms.Form):
    """Form for specifying arguments for executable execution."""
    arguments = forms.CharField(
        max_length=500,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label="Argumentos adicionales"
    )
