from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, FileResponse, JsonResponse
from formtools.wizard.views import SessionWizardView
from .forms import GradeEntryForm, AssignmentHeadForm, AssignmentDetailFormSet, AttendanceForm, TeacherForm, ReportCardComment, StudentReportcardForm, ReportCardGradeForm, ReportCardGradeFormset, CourseByTeacher, ReportCardFilterForm
from .models import *
from admission.models import Class, ClassMember, Teacher, Student, User
from django.db.models import Sum, Avg, Count, Max, Min
from django.db.models import F
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.platypus import Table, TableStyle, SimpleDocTemplate, Frame, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib import colors
from reportlab.graphics.shapes import Drawing, Line
from slick_reporting.views import ReportView, SlickReportView
from slick_reporting.fields import ComputationField
import io

def gb_index(request):
    return render(request, "partials/gradebook/index.html")

def get_courses(request):
    subject_id = request.GET.get('subject_id')
    if subject_id:
        courses = Course.objects.filter(subject_id=subject_id).values('id', 'name')
        return JsonResponse(list(courses), safe=False)
    return JsonResponse([], safe=False)

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
        user=request.user
        # homeroom_check = Class.objects.filter(teacher__user=user, is_home_class=True).first()
            # if a user has a teacher relationship / if in the teacher model the logged in user matches with a data in the Teacher model
        # if homeroom_check:
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
        
        # if step == '0':
        #     initial['academic_year'] = None
        #     initial['period'] = None
        #     initial['teacher'] = None
        #     initial['subject'] = None
        #     initial['course'] = None
        #     initial['assignment_type'] = None


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

    def get_form_kwargs(self, step=None):
        kwargs = super().get_form_kwargs(step)
        if step == '2':
            step1_data = self.get_cleaned_data_for_step('1')
            if step1_data and 'max_score' in step1_data:
                kwargs['max_score'] = step1_data['max_score']
        return kwargs

    def get_context_data(self, form, **kwargs):
        context = super().get_context_data(form=form, **kwargs)
        
        if self.steps.current == '1':
            data_step0 = self.get_cleaned_data_for_step('0')
            if data_step0:
                context['selected_course'] = data_step0.get('course')
        
        if self.steps.current == '0':
            acayear = AcademicYear.objects.all()
            period = LearningPeriod.objects.all().select_related('academic_year')
            subject = Subject.objects.all()
            context['selected_acayear'] = acayear
            context['selected_period'] = period
            context['selected_subject'] = subject
        
        # Kirim data head untuk display di step 3 (index '2')
        if self.steps.current == '2':
            data_step1 = self.get_cleaned_data_for_step('1')
            if data_step1:
                context['assignment_head_data'] = data_step1
                context['max_score'] = data_step1.get('max_score')
                
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
        max_score = assignment_head.max_score
        for form in formset_data_2:
            if form.is_valid() and form.cleaned_data: # Pastikan form valid dan tidak kosong
                note_content = form.cleaned_data.get('teacher_notes')
                detail = form.save(commit=False)
                detail.assignment_head = assignment_head # Link ke Head yang baru dibuat
                detail.teacher_notes = note_content
                if detail.score > max_score:
                    return HttpResponse("Error: Score exceeds maximum allowed.")
                else:
                # Student sudah ada di instance dari form clean (karena ModelForm)
                    details_to_create.append(detail)
        
        # Bulk create untuk performa lebih cepat
        AssignmentDetail.objects.bulk_create(details_to_create)

        
        return render(self.request, "partials/gradebook/finished_screen.html")
    
def midterm_report(request):

    # all_users = User.objects.filter(groups=1).order_by('-angkatan').all() # semuanya kecuali 
    all_students = Student.objects.all()
    
    # This will be the final list we send to the template.
    # student_list = [] 
    # user_rekap_list_by_prodi = [] 
    # user_rekap_list_by_angkatan = [] 

    # Loop through each user to perform calculations.
    # for u in all_students:
    #     # Calculate total 'Aktivitas' points for this specific user.
    #     aktivitas_points = Aktivitas.objects.filter(user=u, status="approved").aggregate(
    #         total=Sum(F('aturan_merit__poin') * F('kuantitas'), default=0)
    #     )['total']
        
    #     # Calculate total 'Pelanggaran' points for this specific user.
    #     pelanggaran_points = Pelanggaran.objects.filter(user=u).aggregate(
    #         total=Sum(F('aturan_demerit__poin') * F('kuantitas'), default=0)
    #     )['total']

    #     modal_poin = u.modal_poin_awal

    #     # Calculate the final total points, starting with a base of 100.
    #     total_points = (aktivitas_points or 0) - (pelanggaran_points or 0) + modal_poin
        
    #     # Append a dictionary with this user's complete data to our list.
    #     user_rekap_list.append({
    #         'user_obj': u,
    #         'aktivitas': aktivitas_points,
    #         'pelanggaran': pelanggaran_points,
    #         'total': total_points,
    #         'modal_poin': modal_poin
    #     })

    # The context now only needs to contain our clean, processed list.
    context = {
        # 'user_rekap_list': user_rekap_list,
        'all_students': all_students
    }
    # print(f"Sort type: {sort_type}, Order field: {order_field}")
    # print(f"All users count: {all_users.count()}")
    # print(f"First user: {all_users.first()}")   
    # return render(request, 'rekap.html', context)
    # if request.headers.get('HX-Request'):
    #     return render(request, 'partials/rekap_table.html', context)


    return render(request, "partials/gradebook/generate_report.html", context)


def midterm_report_pdf(request, student_id=None):
    buf = io.BytesIO()
    # student_id = Student.id

    
    header_data = []
    # If user_id provided, limit to that user's records and set filename accordingly
    if student_id:
        stud_obj = get_object_or_404(Student, id=student_id)
        class_obj = get_object_or_404(Class, id=student_id)
        lperiod_obj = get_object_or_404(LearningPeriod, id=student_id)
        filename = f'ekupoint_report_table_{stud_obj}.pdf'
        
        header_data = [
            ['Nama: ', stud_obj.registration_data.first_name],
            ['NIS: ', stud_obj.id_number],
            ['NISN: ', stud_obj.nisn],
            ['        '],
            ['Kelas: ', class_obj.name],
            ['Semester: ', lperiod_obj.period_name],
            ['Tahun Ajaran: ', lperiod_obj.academic_year],
        ]
    else:
        filename = 'ekupoint_report_table.pdf'

    doc = SimpleDocTemplate(buf, pagesize=(595, 842))
    flowables = []

    styles = getSampleStyleSheet()

    center_style = ParagraphStyle(
        'Center',
        parent=styles['Normal'],
        alignment=TA_CENTER,
        fontName='Times-Roman'
)
    
    center_style_small = ParagraphStyle(
        'Center',
        parent=styles['Normal'],
        alignment=TA_CENTER,
        fontSize=8,
        fontName='Times-Roman'
)

    title_style = ParagraphStyle(
        'TitleStyle',             # A name for the style
        parent=styles['Heading3'],  # Base it on the default "Heading1"
        fontSize=20,                # "Really big" size
        alignment=TA_CENTER,        # Center the text
        fontName='Times-Bold'   # Make sure it's bold
    )

    heading_style = ParagraphStyle(
        'HeadingStyle',             # A name for the style
        parent=styles['Heading3'],  # Base it on the default "Heading1"              # "Really big" size        # Center the text
        fontName='Times-Bold'   # Make sure it's bold
    )

    times_nr = ParagraphStyle(
        'TimesNewRoman',
        fontName='Times-Bold'
    )

    kopsurat_nama_institusi = ParagraphStyle(
        'KopSuratNamaInstitusi',
        parent=styles['Normal'],
        fontSize=24,
        leading=24,
        alignment=TA_CENTER,
        fontName='Times-Roman',
        textColor="#5A0303"
    )
    available_width = doc.width

    separator = Drawing(available_width, 2)

    line = Line(
        x1=1, y1=1,
        x2=available_width, y2=1,
        strokeColor=colors.HexColor("#510000"),
        strokeWidth=1
    )

    separator.add(line)
    
    # # kopsurat versi gambar
    # kop_surat = os.path.join(settings.BASE_DIR, 'media/ekupoint/kopsurat.jpg')

    # # logo STTE, buat rekreasi kopsurat
    # logo = os.path.join(settings.BASE_DIR, 'media/ekupoint/logo-stte-jakarta-bwt-kopsurat.png')

    # setting gambar
    # kopsur = Image(kop_surat)
    # logo_stte = Image(logo, width=120, height=90)
    
    # kopsurat yang diambil dari dokumen2 lain; kalo mau dipake tinggal di uncomment
    # flowables.append(kopsur)

    header_text = "LAPORAN HASIL BELAJAR PESERTA DIDIK"
    akt_text_raw = "Aktivitas Mahasiswa:"
    pel_text_raw = "Pelanggaran Mahasiswa:"
    akt_text = Paragraph(akt_text_raw, times_nr)
    pel_text = Paragraph(pel_text_raw, times_nr)
    # header_2 = f"Nama: {user_obj.get_full_name()}"
    # header_3 = f"NIM: {user_obj.nim}"
    # header_4 = f"Prodi: {user_obj.prodi}"
    # header_5 = f"Angkatan: {user_obj.angkatan}"
    header = Paragraph(header_text, title_style)
    # header_dua = Paragraph(header_2)
    # header_tiga = Paragraph(header_3)
    # header_empat = Paragraph(header_4)
    # header_lima = Paragraph(header_5)

    # data2 rekreasi kop surat
    # kop_left_content = [
    #     logo_stte,
    # ]

    # kop_right_content = [
    #     Paragraph("SEKOLAH TINGGI TEOLOGI EKUMENE JAKARTA", kopsurat_nama_institusi),
    #     Spacer(1, 4),
    #     Paragraph("Mall Artha Gading Lantai 3, Jl. Artha Gading Sel. No. 3, Kelapa Gading, Jakarta Utara, Indonesia 14240", center_style_small),
    #     Paragraph("+628197577740      institusi.stte@sttekumene.ac.id      sttekumene.ac.id", center_style_small),
    # ]

    # kopsurat_data_1 = [
    #     [kop_right_content],
    # ]

    # kopsurat_table = Table(kopsurat_data_1, colWidths=[100, 400])

    # kopsurat_table.setStyle(TableStyle([
    #         ('GRID', (0, 0), (-1, -1), 0.5, "#FFFFFFFF"), # No grid
    #         ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    #         ('ALIGN', (0, 0), (0, 0), 'LEFT'),  # Align labels (col 0) to the left
    #         ('ALIGN', (1, 0), (1, -1), 'LEFT'), # Align values (col 1) to the left
    #         ('FONTNAME', (0, 0), (0, -1), 'Times-Roman') # Make labels bold
    #     ]))
    # # rekreasi kop surat
    # flowables.append(kopsurat_table)
    # flowables.append(separator)
    # flowables.append(Spacer(1, 24))
    
    # judul ("EKUPOINT REPORT")
    flowables.append(header)
    # flowables.append(Spacer(1, 12))
    # flowables.append(header_dua)
    flowables.append(Spacer(1, 24))
    # flowables.append(header_tiga)
    # flowables.append(Spacer(1, 12))
    # flowables.append(header_empat)
    # flowables.append(Spacer(1, 12))
    # flowables.append(header_lima)
    # flowables.append(Spacer(1, 12))

    # not functional
    # title_data = [
    #         ["EKUPOINT REPORT", ""]
    #     ]
    
    # title_table = Table(title_data, colWidths=[100, 740])

    # title_table.setStyle(TableStyle([
    #         ('GRID', (0, 0), (-1, -1), 0.5, "#FFFFFF"), # No grid
    #         ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    #         ('ALIGN', (0, 0), (0, -1), 'LEFT'),  # Align labels (col 0) to the left
    #         ('ALIGN', (1, 0), (1, -1), 'LEFT'), # Align values (col 1) to the left
    #         ('FONTNAME', (0, 0), (0, -1), 'Times-Bold'), # Make labels bold
    #     ]))
    
    # table format, biar rapi
    # if student_id:


    header_table = Table(header_data, colWidths=[100, 300])

    header_table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, "#FFFFFF"), # No grid
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),  # Align labels (col 0) to the left
            ('ALIGN', (1, 0), (1, -1), 'LEFT'), # Align values (col 1) to the left
            ('FONTNAME', (0, 0), (0, -1), 'Times-Bold'), # Make labels bold
            ('FONTNAME', (1, 0), (1, -1), 'Times-Roman')
        ]))
    
    # data2 mahasiswa
    flowables.append(header_table)
    separator.add(line)
    flowables.append(Spacer(1, 24))

    # access student id dari: ReportCardgrade > StudentReportcard > Student
    student_qs = Student.objects.all()
    stdnt_rpc = StudentReportcard.objects.get(student=student_id)
    rpcgrade = ReportcardGrade.objects.get(reportcard=stdnt_rpc)
    rpcard_to_print = ReportcardGrade.objects.filter(reportcard=stdnt_rpc)

    # Aktivitas table
    styles = getSampleStyleSheet()
    small = ParagraphStyle('small', parent=styles['Normal'], fontSize=8, leading=10, fontName='Times-Roman', splitLongWords=1, wordWrap='LTR')
    # headers_aktivitas = ["Aktivitas", "Jenis", "Lingkup", "Poin", "Kuantitas", "Keterangan", "File", "Status", "Tanggal"]
    headers_nilai = ["Mata Pelajaran", "KKM", "Nilai", "Predikat"]
    # aktivitas_total = contactdata.aggregate(
    #     total=Sum(F('aturan_merit__poin') * F('kuantitas'))
    # )['total'] or 0
    

    # pelanggaran_total = pelanggaran.aggregate(
    #     total=Sum(F('aturan_demerit__poin') * F('kuantitas'))
    # )['total'] or 0
    data_nilai = [headers_nilai]

    
    for obj in rpcard_to_print:
        
        data_row = [
            obj.subject,
            obj.final_score,
            obj.final_grade,
            obj.teacher_notes
            
        ]
        data_nilai.append(data_row)

    table_aktivitas = Table(data_nilai, repeatRows=1)
    table_aktivitas.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, '#000000'),
        ('BACKGROUND', (0,0), (-1,0), '#eeeeee'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('FONTNAME', (0, 0), (-1, 0), 'Times-Bold'),
        ('FONTNAME', (0, 1), (-1, -1), 'Times-Roman')
    ]))
    flowables.append(akt_text)
    flowables.append(table_aktivitas)

    # total_para_text = f"<b>Total Aktivitas:</b> {aktivitas_total}"
    # # total_para = Paragraph(f"<b>Total Aktivitas:</b> {aktivitas_total}", styles['Normal'])
    # total_para = Paragraph(total_para_text, times_nr)
    # flowables.append(Spacer(1, 6))
    # flowables.append(total_para)

    # # Spacer between tables
    # flowables.append(Spacer(1, 24))

    # # Pelanggaran table
    # # styles = getSampleStyleSheet()
    # # small = ParagraphStyle('small', parent=styles['Normal'], fontSize=8, leading=10)
    # # headers_pelanggaran = ["Pelanggaran", "Lingkup", "Poin", "Kuantitas", "Keterangan", "Tanggal"]
    # headers_pelanggaran = ["Pelanggaran", "Poin", "Kuantitas", "Keterangan", "Tanggal"]
    # data_pelanggaran = [headers_pelanggaran]
    # for obj in pelanggaran:
    #     aturan_para = Paragraph(str(obj.aturan_demerit) if obj.aturan_demerit else '', small)
    #     pelanggaran_para = Paragraph(obj.aturan_demerit.pelanggaran or '', small)
    #     keterangan_para = Paragraph(obj.keterangan or '', small)
    #     lingkup_para = Paragraph(obj.aturan_demerit.lingkup or '', small)
    #     kuantitas_para = Paragraph(str(obj.kuantitas) or '', small)
    #     created_at_para = Paragraph(obj.created_at.strftime('%Y-%m-%d %H:%M') if obj.created_at else '', small)
    #     data_row = [
    #         # obj.user.get_full_name() if obj.user else '',
    #         aturan_para,
    #         # pelanggaran_para,
    #         # obj.aturan_demerit.lingkup or '',
    #         getattr(obj, 'poin', '') or '',
    #         kuantitas_para,
    #         keterangan_para,
    #         created_at_para,
    #     ]
    #     data_pelanggaran.append(data_row)

    # colWidths = [80, 180, 200, 60, 40, 40, 160, 80, 50, 80]

    # table_pelanggaran = Table(data_pelanggaran, repeatRows=1)
    # table_pelanggaran.setStyle(TableStyle([
    #     # ('BOX', (0, 0), (-1, 0), 1.1, '#000000'),
    #     ('GRID', (0,0), (-1,-1), 0.5, '#000000'),
    #     ('BACKGROUND', (0,0), (-1,0), '#eeeeee'),
    #     ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    #     ('FONTSIZE', (0,0), (-1,-1), 8),
    #     ('FONTNAME', (0, 0), (-1, 0), 'Times-Bold'),
    #     ('FONTNAME', (0, 1), (-1, -1), 'Times-Roman')
    # ]))
    # flowables.append(pel_text)
    # flowables.append(table_pelanggaran)

    #     # add Pelanggaran total
    # total_pel_para_text = f"<b>Total Pelanggaran:</b> {pelanggaran_total}"
    # # total_pel_para = Paragraph(f"<b>Total Pelanggaran:</b> {pelanggaran_total}", styles['Normal'])
    # total_pel_para = Paragraph(total_pel_para_text, times_nr)
    # flowables.append(Spacer(1, 6))
    # flowables.append(total_pel_para)

    # # grand total
    # grand_total = aktivitas_total - pelanggaran_total + modal_poin
    # grand_para_text = f"<b>Total (+ Modal Poin {modal_poin}):</b> {grand_total}"
    # # grand_para = Paragraph(f"<b>Total (+ Modal Poin {modal_poin}):</b> {grand_total}", styles['Heading3'])
    # grand_para = Paragraph(grand_para_text, times_nr)
    # flowables.append(Spacer(1, 12))
    # flowables.append(grand_para)

    # sig_left_content = [
    #     Paragraph("Dosen Wali", center_style),
    #     Paragraph("Akademik", center_style),
    #     Spacer(1, 80),  
    #     Paragraph("(_________________)", center_style),
    # ]

    # sig_right_content = [
    #     Paragraph(f"Jakarta, {timezone.now().strftime('%d %B %Y')}", center_style,),
    #     Paragraph("Wakil Ketua Bidang Kemahasiswaan, ", center_style),
    #     Paragraph("Alumni, dan Kerja Sama", center_style),
    #     Spacer(1, 60), # 60-point gap for signature
    #     Paragraph("(_________________)", center_style),
    # ]

    # footer_data_1 = [
    #     [sig_left_content,'  ', sig_right_content],
    # ]

    # footer1_table = Table(footer_data_1)

    # footer1_table.setStyle(TableStyle([
    #         ('GRID', (0, 0), (-1, -1), 0.5, "#FFFFFF"), # No grid
    #         ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    #         ('ALIGN', (0, 0), (0, -1), 'LEFT'),  # Align labels (col 0) to the left
    #         ('ALIGN', (1, 0), (1, -1), 'LEFT'), # Align values (col 1) to the left
    #         ('FONTNAME', (0, 0), (0, -1), 'Times-Roman') # Make labels bold
    #     ]))
    # flowables.append(Spacer(1, 24))
    # flowables.append(footer1_table)
    # flowables.append(Spacer(1, 24))

    doc.build(flowables)
    buf.seek(0)
    return FileResponse(buf, as_attachment=True, filename=filename)


class ReportCardForm(SessionWizardView):
    # Definisikan template untuk setiap step (opsional, bisa pakai satu template saja)
    template_name = "partials/gradebook/report_card.html"
    
    form_list = [
        ("0", StudentReportcardForm),
        ("1", CourseByTeacher),
        ("2", ReportCardGradeFormset),
    ]

    # def get_template_names(self):
    #     return [self.templates[self.steps.current]]

    # def get_form(self, step=None, data=None, files=None):
    #     form = super().get_form(step, data, files)
    #     if step == '1' and form.initial.get('subject'):
    #         form.fields['course'].queryset = Course.objects.filter(subject=form.initial['subject'])
    #     return form

    def get_form_initial(self, step):
        initial = super().get_form_initial(step)


        
        # Logika khusus untuk Step 3 (FormSet Siswa)
        if step == '2':
            # Ambil data dari Step 0 (GradeEntry)
            step0_data = self.get_cleaned_data_for_step('1')
            if step0_data and 'subject' in step0_data:
                subject = step0_data['subject']
                course = step0_data.get('course')
                
                if course:
                    # Ambil semua siswa yang aktif di course tersebut
                    students = CourseMember.objects.filter(
                        course=course
                    ).select_related('student')
                else:
                    # If no course selected, get all students from all courses of the subject
                    courses = Course.objects.filter(subject=subject)
                    students = CourseMember.objects.filter(
                        course__in=courses
                    ).select_related('student')
                
                # Siapkan initial data (list of dicts) untuk FormSet
                initial_list = []
                for member in students:
                    initial_list.append({
                        'student_name': str(member.student),  # Display name from related Student
                        'subject': subject.id,  # Subject ID from step 1
                    })
                return initial_list
        
        return initial

    def get_context_data(self, form, **kwargs):
        context = super().get_context_data(form=form, **kwargs)
        
        if self.steps.current != '0':
            data_step0 = self.get_cleaned_data_for_step('1')
            if data_step0:
                context['selected_course'] = data_step0.get('course')

        if self.steps.current == '1':
            subject = Subject.objects.all()
            course = Course.objects.all().select_related('subject')
            context['selected_subject'] = subject
            context['selected_course'] = course
        
        # Kirim data head untuk display di step 3 (index '2')
        if self.steps.current == '2':
            data_step1 = self.get_cleaned_data_for_step('1')
            if data_step1:
                context['assignment_head_data'] = data_step1
                
        return context

    def done(self, form_list, **kwargs):
        # Ambil data dari form yang sudah divalidasi
        form_data_0 = form_list[0].cleaned_data # StudentReportcardForm (academic_year, period, is_mid, level)
        form_data_1 = form_list[1].cleaned_data # CourseByTeacher (course, subject)

        # Get the course and subject from step 1
        course = form_data_1['course']
        subject = form_data_1['subject']

        # Get all students in the course
        students_in_course = CourseMember.objects.filter(course=course).select_related('student')

        # Create a StudentReportcard for each student
        reportcards = {}
        for member in students_in_course:
            student_reportcard = StudentReportcard(
                academic_year=form_data_0['academic_year'],
                period=form_data_0['period'],
                is_mid=form_data_0['is_mid'],
                level=form_data_0['level'],
                student=member.student
            )
            student_reportcard.save()
            reportcards[member.student.id] = student_reportcard

        # 3. Simpan ReportcardGrade (Looping FormSet)
        details_to_create = []
        
        print("\n--- DEBUG: Starting FormSet Loop ---")
        
        formset = form_list[2]  # ReportCardGradeFormset
        
        # Zip the formset forms with the students (assuming order matches initial_list)
        for i, (form, member) in enumerate(zip(formset.forms, students_in_course)):
            
            # Re-validate the form here to force errors to populate the form object
            is_valid = form.is_valid()
            
            print(f"DEBUG: Form Index {i}: Valid? {is_valid}")

            if is_valid and form.cleaned_data:
                # Print the data to confirm required fields are present
                print(f"DEBUG: Form {i} Cleaned Data: {form.cleaned_data}")

                # Extract the subject from this form's cleaned_data
                # subject_obj = form.cleaned_data.get('subject')
                subject_obj = subject  # Use the subject from step 1 directly
                
                # Check if the subject object is None
                if not subject_obj:
                    print(f"!!! CRITICAL FAIL: Form {i} cleaned_data['subject'] is missing or None.")
                    continue

                detail = form.save(commit=False)
                detail.reportcard = reportcards[member.student.id]  # Assign the correct reportcard
                detail.subject = subject_obj

                # If the form corresponds to an existing DB row, save/update it.
                if detail.pk:
                    detail.save()
                else:
                    # Ensure PK is None for new objects to let the DB assign it
                    detail.pk = None
                    details_to_create.append(detail)
            
            else:
                # Print form errors if not valid
                print(f"DEBUG: Form {i} Errors: {form.errors}")
                
            print(f"--- DEBUG: Total forms added to bulk_create: {len(details_to_create)} ---\n")
        
        # Bulk-create any new grade rows (do not attempt to bulk_create existing PKs)
        if details_to_create:
            ReportcardGrade.objects.bulk_create(details_to_create)
            
        return render(self.request, "partials/gradebook/finished_screen_teachercomm.html")

def get_courses(request):
    subject_id = request.GET.get('0-subject') or request.GET.get('1-subject') or request.GET.get('subject')
    selected_course = request.GET.get('0-course') or request.GET.get('1-course') or request.GET.get('course')
    if subject_id:
        courses = Course.objects.filter(subject_id=subject_id)
    else:
        courses = Course.objects.all()
    context = {
        'courses': courses,
        'selected_course': selected_course
    }
    return render(request, "partials/gradebook/course_list.html", context)

def get_period_ge(request):
    # acayear_id = AcademicYear.objects.first().id
    acayear_id = request.GET.get('0-academic_year') or request.GET.get('1-academic_year') or request.GET.get('academic_year')
    selected_period = request.GET.get('0-period') or request.GET.get('1-period') or request.GET.get('period')
    if acayear_id:
        periods = LearningPeriod.objects.filter(academic_year_id=acayear_id)
    else:
        periods = LearningPeriod.objects.none()
    context = {
        'periods': periods,
        'selected_period': selected_period
    }
    return render(request, "partials/gradebook/gradeentry_partials/period.html", context)


def get_subjects_ge(request):
    teacher_id = request.GET.get('0-teacher') or request.GET.get('1-teacher') or request.GET.get('teacher')
    selected_subject = request.GET.get('0-subject') or request.GET.get('1-subject') or request.GET.get('subject')
    if teacher_id:
        # subjects = Subject.objects.filter(course__coursemember__student__coursemember__course__coursemember__course__teacher__id=teacher_id).distinct()
        subjects = Subject.objects.filter(course__teacher__id=teacher_id).distinct()
    else:
        subjects = Subject.objects.all()
    context = {
        'subjects': subjects,
        'selected_subject': selected_subject
    }
    return render(request, "partials/gradebook/gradeentry_partials/subject.html", context)


def get_courses_ge(request):
    subject_id = request.GET.get('0-subject') or request.GET.get('1-subject') or request.GET.get('subject')
    selected_course = request.GET.get('0-course') or request.GET.get('1-course') or request.GET.get('course')
    if subject_id:
        courses = Course.objects.filter(subject_id=subject_id)
    else:
        courses = Course.objects.all()
    context = {
        'courses': courses,
        'selected_course': selected_course
    }
    return render(request, "partials/gradebook/course_list.html", context)


class ReportCardGradeSummary(ReportView):
    # template_name = "partials/gradebook/report_summary.html"

    # def get_columns(self):
    #     columns = [
    #         "reportcard__student__registration_data__first_name",
    #     ]
    #     subjects = Subject.objects.all()
    #     for subject in subjects:
    #         columns.append(
    #             ComputationField.create(
    #                 Sum, "final_score", 
    #                 name=f"subject_{subject.id}_score", 
    #                 verbose_name=subject.subject_name, 
    #                 is_summable=True
    #             )
    #         )
    #     return columns

    report_model = ReportcardGrade

    date_field = "reportcard__period__date_end"
    
    group_by = "reportcard__student__registration_data__first_name"

    subjects = Subject.objects.all()

    # form_class = ReportCardFilterForm

    columns = [
        # 2. Ensure this matches the group_by field to display the text label
        "reportcard__student__id_number", 
        "reportcard__student__registration_data__first_name", 
        "reportcard__student__registration_data__last_name"
    ]

    
    for subject in subjects:
        columns.append(
            ComputationField.create(
                Sum, "final_score",  # Aggregates (sums) the final_score for each student-subject
                name=f"subject_{subject.id}_score", 
                verbose_name=subject.short_name,  # Displays the subject name as the column header
                is_summable=False
            )
        )

    # columns.append(
    #     ComputationField.create(
    #         Sum, "final_score",  # Total final_score across all subjects for each student
    #         name="total_score", 
    #         verbose_name="Total Score", 
    #         is_summable=False
    #     )
    # )

    # crosstab_field = "subject_id"

    # computation_fields = [
    #     ComputationField.create(
    #         Sum, "final_score", name="final_score", verbose_name="Final Score", is_summable=True
    #     )
    # ]

    # crosstab_ids = ["Mathematics", "Biology", "Geography", "Chemistry"]  # Example subject names
    # crosstab_computer_remainder = True
    # crosstab_columns = [
    #         ComputationField.create(
    #         Count, "subject", name="final_score", verbose_name="Final Score", is_summable=True,
    #     )
    # ]
    
    # crosstab_ids = Subject.objects.values_list('subject_name', flat=True)



    export_actions = ["export_pdf"]

    def export_pdf(self, report_data):
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="grade_report.pdf"'

        # 2. Create a buffer to hold the PDF data
        buffer = io.BytesIO()
        
        # Use Landscape A4 because crosstabs tend to be wide
        doc = SimpleDocTemplate(buffer, pagesize=(800, 600))
        elements = []

        # 3. Prepare the Data for the Table
        # report_data['columns'] holds the definitions. 
        # report_data['data'] holds the list of dictionaries (rows).
        
        columns = report_data['columns']
        
        # A. Create the Header Row
        # We extract 'verbose_name' to show "Biology" instead of "subject_1"
        headers = [col['verbose_name'] for col in columns]
        table_data = [headers]

        # B. Create the Data Rows
        # We must loop through columns to ensure order matches headers
        for record in report_data['data']:
            row = []
            for col in columns:
                # Use the column 'name' (id) to fetch value from the record dictionary
                key = col['name']
                value = record.get(key, "-") # Default to "-" if empty
                row.append(str(value))       # Ensure it's a string
            table_data.append(row)

        # 4. Create and Style the Table
        # 'colWidths' can be set to None (auto) or specific values
        table = Table(table_data)

        # Add styling: Grid, Bold Header, Alternating Row Colors
        style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),       # Header background
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),  # Header text color
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),              # Center align all text
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),    # Header font
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),             # Header padding
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),     # Default row background
            ('GRID', (0, 0), (-1, -1), 1, colors.black),        # Add grid lines
        ])
        table.setStyle(style)

        # 5. Add Title and Table to the Document
        styles = getSampleStyleSheet()
        elements.append(Paragraph("Student Grade Crosstab Report", styles['Title']))
        elements.append(table)

        # 6. Build the PDF
        doc.build(elements)

        # 7. Get the value of the BytesIO buffer and write it to the response
        pdf = buffer.getvalue()
        buffer.close()
        response.write(pdf)
        
        return response

    export_pdf.title = ("Export PDF")
    export_pdf.icon = "fa fa-file-pdf-o"
    export_pdf.css_class = "btn btn-primary"

    def export_csv(self, report_data):
        return super().export_csv(report_data)

    export_csv.title = ("Export Report Card to CSV")
    export_csv.css_class = "btn btn-success"

    filters = [
        "final_score",
    ]

    report_title = "Student Report Card Crosstab"

def report_card_summary(request):
    report = ReportCardGradeSummary()
    report.request = request
    report.GET = request.GET
    return render(request, 'partials/gradebook/report_summary.html', {'report': report})

def report_card_summary_pdf_rplab(request):
    buf = io.BytesIO()
    # student_id = Student.id

    filename = f"Report_Card.pdf"


    doc = SimpleDocTemplate(buf, pagesize=(900, 600))
    flowables = []

    styles = getSampleStyleSheet()

    center_style = ParagraphStyle(
        'Center',
        parent=styles['Normal'],
        alignment=TA_CENTER,
        fontName='Times-Roman'
)
    
    center_style_small = ParagraphStyle(
        'Center',
        parent=styles['Normal'],
        alignment=TA_CENTER,
        fontSize=8,
        fontName='Times-Roman'
)

    title_style = ParagraphStyle(
        'TitleStyle',             # A name for the style
        parent=styles['Heading3'],  # Base it on the default "Heading1"
        fontSize=20,                # "Really big" size
        alignment=TA_CENTER,        # Center the text
        fontName='Times-Bold'   # Make sure it's bold
    )

    heading_style = ParagraphStyle(
        'HeadingStyle',             # A name for the style
        parent=styles['Heading3'],  # Base it on the default "Heading1"              # "Really big" size        # Center the text
        fontName='Times-Bold'   # Make sure it's bold
    )

    times_nr = ParagraphStyle(
        'TimesNewRoman',
        fontName='Times-Bold'
    )

    kopsurat_nama_institusi = ParagraphStyle(
        'KopSuratNamaInstitusi',
        parent=styles['Normal'],
        fontSize=24,
        leading=24,
        alignment=TA_CENTER,
        fontName='Times-Roman',
        textColor="#5A0303"
    )
    available_width = doc.width

    separator = Drawing(available_width, 2)

    line = Line(
        x1=1, y1=1,
        x2=available_width, y2=1,
        strokeColor=colors.HexColor("#510000"),
        strokeWidth=1
    )

    separator.add(line)
    
    # # kopsurat versi gambar
    # kop_surat = os.path.join(settings.BASE_DIR, 'media/ekupoint/kopsurat.jpg')

    # # logo STTE, buat rekreasi kopsurat
    # logo = os.path.join(settings.BASE_DIR, 'media/ekupoint/logo-stte-jakarta-bwt-kopsurat.png')

    # setting gambar
    # kopsur = Image(kop_surat)
    # logo_stte = Image(logo, width=120, height=90)
    
    # kopsurat yang diambil dari dokumen2 lain; kalo mau dipake tinggal di uncomment
    # flowables.append(kopsur)

    header_text = "LAPORAN HASIL BELAJAR PESERTA DIDIK"
    akt_text_raw = "Aktivitas Mahasiswa:"
    pel_text_raw = "Pelanggaran Mahasiswa:"
    akt_text = Paragraph(akt_text_raw, times_nr)
    pel_text = Paragraph(pel_text_raw, times_nr)
    # header_2 = f"Nama: {user_obj.get_full_name()}"
    # header_3 = f"NIM: {user_obj.nim}"
    # header_4 = f"Prodi: {user_obj.prodi}"
    # header_5 = f"Angkatan: {user_obj.angkatan}"
    header = Paragraph(header_text, title_style)
    # header_dua = Paragraph(header_2)
    # header_tiga = Paragraph(header_3)
    # header_empat = Paragraph(header_4)
    # header_lima = Paragraph(header_5)

    # data2 rekreasi kop surat
    # kop_left_content = [
    #     logo_stte,
    # ]

    # kop_right_content = [
    #     Paragraph("SEKOLAH TINGGI TEOLOGI EKUMENE JAKARTA", kopsurat_nama_institusi),
    #     Spacer(1, 4),
    #     Paragraph("Mall Artha Gading Lantai 3, Jl. Artha Gading Sel. No. 3, Kelapa Gading, Jakarta Utara, Indonesia 14240", center_style_small),
    #     Paragraph("+628197577740      institusi.stte@sttekumene.ac.id      sttekumene.ac.id", center_style_small),
    # ]

    # kopsurat_data_1 = [
    #     [kop_right_content],
    # ]

    # kopsurat_table = Table(kopsurat_data_1, colWidths=[100, 400])

    # kopsurat_table.setStyle(TableStyle([
    #         ('GRID', (0, 0), (-1, -1), 0.5, "#FFFFFFFF"), # No grid
    #         ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    #         ('ALIGN', (0, 0), (0, 0), 'LEFT'),  # Align labels (col 0) to the left
    #         ('ALIGN', (1, 0), (1, -1), 'LEFT'), # Align values (col 1) to the left
    #         ('FONTNAME', (0, 0), (0, -1), 'Times-Roman') # Make labels bold
    #     ]))
    # # rekreasi kop surat
    # flowables.append(kopsurat_table)
    # flowables.append(separator)
    # flowables.append(Spacer(1, 24))
    
    # judul ("EKUPOINT REPORT")
    flowables.append(header)
    # flowables.append(Spacer(1, 12))
    # flowables.append(header_dua)
    flowables.append(Spacer(1, 24))

    # access student id dari: ReportCardgrade > StudentReportcard > Student
    stdnt_rpc = StudentReportcard.objects.all()
    rpcgrade = ReportcardGrade.objects.all()
    rpcard_to_print = ReportcardGrade.objects.all()

    # Aktivitas table
    styles = getSampleStyleSheet()
    subjects = Subject.objects.all()
    small = ParagraphStyle('small', parent=styles['Normal'], fontSize=8, leading=10, fontName='Times-Roman', splitLongWords=1, wordWrap='LTR')
    # headers_aktivitas = ["Aktivitas", "Jenis", "Lingkup", "Poin", "Kuantitas", "Keterangan", "File", "Status", "Tanggal"]
    headers_nilai = ["NISN", "Nama Siswa"]

    for subs in subjects:
        subs.subject_name
        headers_nilai.append(subs.subject_name)
    # aktivitas_total = contactdata.aggregate(
    #     total=Sum(F('aturan_merit__poin') * F('kuantitas'))
    # )['total'] or 0
    

    # pelanggaran_total = pelanggaran.aggregate(
    #     total=Sum(F('aturan_demerit__poin') * F('kuantitas'))
    # )['total'] or 0
    data_nilai = [headers_nilai]
    # kolom_nilai = [len(headers_nilai)]

    
    # for obj in rpcard_to_print:
        
    #     data_row = [
    #         obj.reportcard.student.id_number,
    #         str(obj.reportcard.student),
            
    #     ]
    #     data_nilai.append(data_row)
    #     data_row = [
    #         obj.final_score,
    #     ]
    #     kolom_nilai.append(data_row)

    student_report_cards = ReportcardGrade.objects.all()

    for rpc in student_report_cards:
        student = rpc.reportcard.student
        
        # Start the row with Student Info
        row = [
            student.id_number, 
            str(student)
        ]

        # single_score = getattr(rpc, 'final_score')
        single_score = getattr(rpc, 'final_score')

        # 4. FILL THE ROW (MATCHING HEADERS)
        # Loop through the *Subjects* defined in step 1 to maintain column order
        for sub in subjects:
            row.append(single_score)

        # Append the fully constructed row to the table data
        data_nilai.append(row)

    table_aktivitas = Table(data_nilai, repeatRows=1)
    table_aktivitas.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, '#000000'),
        ('BACKGROUND', (0,0), (-1,0), '#eeeeee'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('FONTNAME', (0, 0), (-1, 0), 'Times-Bold'),
        ('FONTNAME', (0, 1), (-1, -1), 'Times-Roman')
    ]))
    flowables.append(akt_text)
    flowables.append(table_aktivitas)


    doc.build(flowables)
    buf.seek(0)
    return FileResponse(buf, as_attachment=True, filename=filename)


def report_card_nonslick(request):
# 1. SETUP: Define the context (Year, Period, etc.)
    # You might get these from request.GET or defaults
    current_year = AcademicYear.objects.first() 
    current_period = LearningPeriod.objects.filter(academic_year=current_year).first()

    # 2. COLUMNS: Get all subjects ordered consistently
    subjects = Subject.objects.all().order_by('id')

    # 3. ROWS: Get the students you want to display
    # (e.g., filtered by a specific class if needed)
    students = Student.objects.filter(is_active=True).select_related('registration_data')

    # 4. DATA: Fetch ALL relevant grades in one query
    # We filter by the specific period to avoid mixing Mid/Final grades
    grades = ReportcardGrade.objects.filter(
        reportcard__period=current_period,
        reportcard__student__in=students
    ).select_related('reportcard', 'subject')

    # 5. MAP: Create a lookup dictionary for fast access
    # Key = (student_id, subject_id) -> Value = final_score
    grade_map = {}
    for g in grades:
        grade_map[(g.reportcard.student_id)] = g.final_score

    # 6. PIVOT: Build the final list for the template
    report_data = []
    for student in students:
        # Create a list of scores that matches the 'subjects' order exactly
        student_scores = []
        for subj in subjects:
            # Get score from map, default to 0 if not found
            score = grade_map.get((student.id), 0)
            student_scores.append(score)

        report_data.append({
            'id_number': student.id_number,
            'first_name': student.registration_data.first_name,
            'last_name': student.registration_data.last_name,
            'scores': student_scores, # This list is perfectly aligned with table headers
        })

    context = {
        'subjects': subjects,
        'student_rows': report_data,
        'current_period': current_period,
    }
    return render(request, 'partials/gradebook/report_card_nonslick.html', context)


