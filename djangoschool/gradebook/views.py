from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from formtools.wizard.views import SessionWizardView
from .forms import GradeEntryForm, AssignmentHeadForm, AssignmentDetailFormSet, AttendanceForm, TeacherForm
from .models import CourseMember, AssignmentHead, AssignmentDetail, GradeEntry, StudentAttendance
from admission.models import Class, ClassMember, Teacher, Student


def gb_index(request):
    return render(request, "partials/gradebook/index.html")

def teacher_list(request):
    return HttpResponse("pass")

def course_list(request):
    return HttpResponse("pass")

def grade_entry(request):
    entry = GradeEntry.objects.get(pk=3)
    form = GradeEntryForm(instance=entry)
    context = {'form': form }
    return render(request, "partials/gradebook/entry.html", context)

def get_period(request):
    pass

def attendance(request):
    # cannot unpack non-iterable ForwardManyToOneDescriptor object
    # current_teacher = get_object_or_404(Teacher, user=request.user)
    # filtered_students = Teacher.objects.filter(current_teacher)
    if request.method == 'POST':
        
        form = AttendanceForm(request.POST, user=request.user)
        # teach_form = TeacherForm(request.POST)
        
        if form.is_valid():
            form.save()
            
    form = AttendanceForm(user=request.user)
    # teach_form = TeacherForm()

    # if 'student' in form.fields:
    #     form.fields['student'].queryset = filtered_students


    context = {
        'form': form,
        # 'classes': filtered_students
    }
    return render(request, 'partials/gradebook/attendance.html', context)


class GradeEntryForm(SessionWizardView):
    # Definisikan template untuk setiap step (opsional, bisa pakai satu template saja)
    template_name = "partials/gradebook/grade_entry.html"
    
    form_list = [
        ("0", GradeEntryForm),
        ("1", AssignmentHeadForm),
        ("2", AssignmentDetailFormSet), # Step 3 pakai FormSet
    ]

    # def get_template_names(self):
    #     return [self.templates[self.steps.current]]

    def get_form_initial(self, step):
        initial = super().get_form_initial(step)
        
        # Logika khusus untuk Step 3 (FormSet Siswa)
        if step == '2':
            # Ambil data dari Step 0 (GradeEntry)
            step0_data = self.get_cleaned_data_for_step('0')
            if step0_data and 'course' in step0_data:
                course = step0_data['course']
                
                # Ambil semua siswa yang aktif di course tersebut
                students = CourseMember.objects.filter(
                    course=course, 
                    is_active=True
                ).select_related('student')
                
                # Siapkan initial data (list of dicts) untuk FormSet
                initial_list = []
                for member in students:
                    initial_list.append({
                        'student': member.student.id, # Untuk Hidden Field
                        'is_active': member.is_active,
                    })
                return initial_list
        
        return initial

    def get_context_data(self, form, **kwargs):
        context = super().get_context_data(form=form, **kwargs)
        
        if self.steps.current != '0':
            data_step0 = self.get_cleaned_data_for_step('0')
            if data_step0:
                context['selected_course'] = data_step0.get('course')
        
        # Kirim data head untuk display di step 3 (index '2')
        if self.steps.current == '2':
            data_step1 = self.get_cleaned_data_for_step('1')
            if data_step1:
                context['assignment_head_data'] = data_step1
                
        return context

    def done(self, form_list, **kwargs):
        # Ambil data dari form yang sudah divalidasi
        form_data_0 = form_list[0].cleaned_data # GradeEntry
        form_data_1 = form_list[1].cleaned_data # AssignmentHead
        formset_data_2 = form_list[2] # AssignmentDetailFormSet (ini formset object)

        # 1. Simpan GradeEntry (jika masih diperlukan sebagai log)
        # grade_entry_instance = form_list[0].save()

        # 2. Buat dan Simpan AssignmentHead
        # Kita gabungkan data dari Step 0 dan Step 1
        assignment_head = AssignmentHead(
            assignment=form_data_0['assignment_type'], # Dari Step 0
            course=form_data_0['course'],              # Dari Step 0
            date=form_data_1['date'],                  # Dari Step 1
            topic=form_data_1['topic'],                # Dari Step 1
            max_score=form_data_1['max_score']         # Dari Step 1
        )
        assignment_head.save()

        # 3. Simpan AssignmentDetail (Looping FormSet)
        details_to_create = []
        for form in formset_data_2:
            if form.is_valid() and form.cleaned_data: # Pastikan form valid dan tidak kosong
                detail = form.save(commit=False)
                detail.assignment_head = assignment_head # Link ke Head yang baru dibuat
                # Student sudah ada di instance dari form clean (karena ModelForm)
                details_to_create.append(detail)
        
        # Bulk create untuk performa lebih cepat
        AssignmentDetail.objects.bulk_create(details_to_create)

        
        return render(self.request, "partials/gradebook/finished_screen.html")
    

