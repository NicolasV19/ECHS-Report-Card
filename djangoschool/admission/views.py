from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from formtools.wizard.views import SessionWizardView
from .forms import PersonalInfoForm, ContactInfoForm, ParentInfoForm
from .models import *
from .charts import months, colorPrimary, colorSuccess, colorDanger, generate_color_palette, get_year_dict
from django.db.models.functions import ExtractYear, ExtractMonth

# Create your views here.
def index(request):
    return HttpResponse("Welcome to Admission apps portal.")

class AdmissionView(SessionWizardView):
    template_name = "partials/admission/admission.html"

    form_list = [
        ("0", PersonalInfoForm),
        ("1", ContactInfoForm),
        ("2", ParentInfoForm), # Step 3 pakai FormSet
    ]

    def done(self, form_list, **kwargs):
        if form_list:
            form_data = {}
            for form in form_list:
                form_data.update(form.cleaned_data)
            # Simpan data ke model Registration

            registration = Registration.objects.create(
                form_no=form_data.get('form_no'),
                first_name=form_data.get('first_name'),
                last_name=form_data.get('last_name'),
                middle_name=form_data.get('middle_name'),
                gender=form_data.get('gender'),
                nisn=form_data.get('nisn'),
                prev_school=form_data.get('prev_school'),
                prev_nis=form_data.get('prev_nis'),
                birth_order=form_data.get('birth_order'),
                date_of_birth=form_data.get('date_of_birth'),
                place_of_birth=form_data.get('place_of_birth'),
                religion=form_data.get('religion'),
                church_name=form_data.get('church_name'),
                current_address=form_data.get('current_address'),
                current_district=form_data.get('current_district'),
                current_region=form_data.get('current_region'),
                current_city=form_data.get('current_city'),
                current_province=form_data.get('current_province'),
                contact_whatsapp=form_data.get('contact_whatsapp'),
                contact_mobile=form_data.get('contact_mobile'),
                contact_email=form_data.get('contact_email'),
                contact_preference=form_data.get('contact_preference'),
                mother_name=form_data.get('mother_name'),
                mother_nik=form_data.get('mother_nik'),
                mother_religion=form_data.get('mother_religion'),
                mother_education=form_data.get('mother_education'),
                mother_occupation=form_data.get('mother_occupation'),
                mother_address_same2applicant=form_data.get('mother_address_same2applicant'),
                mother_address=form_data.get('mother_address'),
                mother_district=form_data.get('mother_district'),
                mother_region=form_data.get('mother_region'),
                mother_city=form_data.get('mother_city'),
                mother_province=form_data.get('mother_province'),
                mother_phone=form_data.get('mother_phone'),
                mother_mobile=form_data.get('mother_mobile'),
                mother_whatsapp=form_data.get('mother_whatsapp'),
                mother_email=form_data.get('mother_email'),
                father_name=form_data.get('father_name'),
                father_nik=form_data.get('father_nik'),
                father_religion=form_data.get('father_religion'),
                father_education=form_data.get('father_education'),
                father_occupation=form_data.get('father_occupation'),
                father_address_same2applicant=form_data.get('father_address_same2applicant'),
                father_address=form_data.get('father_address'),
                father_district=form_data.get('father_district'),
                father_region=form_data.get('father_region'),
                father_city=form_data.get('father_city'),
                father_province=form_data.get('father_province'),
                father_phone=form_data.get('father_phone'),
                father_mobile=form_data.get('father_mobile'),
                father_whatsapp=form_data.get('father_whatsapp'),
                father_email=form_data.get('father_email'),
            )

        registration.save()

        
        return render(self.request, "partials/admission/finished_screen.html")
    

from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from formtools.wizard.views import SessionWizardView
from .forms import PersonalInfoForm, ContactInfoForm, ParentInfoForm
from .models import *
from .charts import months, colorPrimary, colorSuccess, colorDanger, generate_color_palette, get_year_dict
from django.db.models.functions import ExtractYear, ExtractMonth
from django.db.models import Count, Sum, Avg  # Add this import

# ...existing code...

def get_filter_options(request):
    options = AcademicYear.objects.all().order_by('-year').values_list('year', flat=True)

    return JsonResponse({
        "options": list(options)
    })

# Add this new view for student counts per grade level
def get_student_counts(request):
    year = request.GET.get('year')
    queryset = ClassMember.objects.filter(is_active=True)
    if year:
        queryset = queryset.filter(kelas__academic_year__year=year, kelas__is_home_class=True)
    counts = queryset.values('kelas__name').annotate(count=Count('student')).order_by('kelas__name')
    
    labels = [item['kelas__name'] for item in counts]
    data = [item['count'] for item in counts]
    
    return JsonResponse({
        'labels': labels,
        'data': data,
    })