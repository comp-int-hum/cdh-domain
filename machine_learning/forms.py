from django.forms import ModelForm, modelform_factory, FileField, CharField, TextInput
from .models import MachineLearningModel
from .widgets import MachineLearningModelInteractionWidget

class MachineLearningModelForm(ModelForm):
    interaction = CharField(widget=TextInput(attrs={"class" : "model-input"}))
    
    def __init__(self, *args, **kwargs):
        prefix = "{}-{}-{}".format(
            MachineLearningModel._meta.app_label,
            MachineLearningModel._meta.model_name,
            kwargs["instance"].id if kwargs.get("instance", False) else "unbound"
        )
        super(MachineLearningModelForm, self).__init__(*args, prefix=prefix, **{k : v for k, v in kwargs.items() if k != "prefix"})
        #print(self.instance)
        self.fields["interaction"].widget.attrs.update(
            {
                #"hx-post" : self.instance.get_absolute_url(),
                #"hx-trigger" : "keyup changed delay:1000ms",
                #"hx-target" : "",
            }
        )
        #print(self.fields["output_content"])

    #def render(self, *argv, **argd):
    #    print(self.fields["output_content"].widget.render())
    #    return super(MachineLearningModelForm, self).render(*argv, **argd)
        
    class Meta:
        model = MachineLearningModel
        fields = []

