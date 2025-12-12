from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, FileResponse
from formtools.wizard.views import SessionWizardView
from .forms import GradeEntryForm, AssignmentHeadForm, AssignmentDetailFormSet, AttendanceForm, TeacherForm, ReportCardComment, StudentReportcardForm, ReportCardGradeForm, ReportCardGradeFormset
from .models import *
from admission.models import Class, ClassMember, Teacher, Student, User
from django.db.models import Sum
from django.db.models import F
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.platypus import Table, TableStyle, SimpleDocTemplate, Frame, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib import colors
from reportlab.graphics.shapes import Drawing, Line
import io


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
                note_content = form.cleaned_data.get('teacher_notes')
                detail = form.save(commit=False)
                detail.assignment_head = assignment_head # Link ke Head yang baru dibuat
                detail.teacher_notes = note_content
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

    stud_rpc = StudentReportcard.objects.all()
    rpcard = ReportcardGrade.objects.all()
    strpc_student = StudentReportcard.student

    # matpel = ReportcardGrade.objects.get(strpc_student)
    # kkm = AssignmentHead.objects.all()
    nilai = ReportcardGrade.final_score
    predikat = ReportcardGrade.final_grade


    course_obj = CourseMember.objects.filter(student__id=student_id).select_related('course')
    kkm = AssignmentHead.objects.all()
    stud_scor = AssignmentDetail.objects.filter(student__id=student_id)

    rpcard_to_print = ReportcardGrade.objects.get(reportcard__id=student_id)

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

    
    for obj, in rpcard_to_print:
        
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
        ("1", ReportCardGradeFormset),
    ]

    # def get_template_names(self):
    #     return [self.templates[self.steps.current]]

    def get_form_initial(self, step):
        initial = super().get_form_initial(step)
        
        # LOGIC FOR STEP 1 (The FormSet of Grades/Subjects)
        if step == '1':
            step0_data = self.get_cleaned_data_for_step('0')
            
            # Safety check: Ensure a student was selected in Step 0
            if not step0_data or 'student' not in step0_data:
                return []

            current_student = step0_data['student']
            
            # DEBUG: Confirm which student is being processed
            print(f"DEBUG: Generating FormSet for Student: {current_student} (ID: {current_student.id})")

            # 1. Find the Courses for the currently selected student
            # We filter only by student ID
            student_id_for_filter = current_student.id

# Add this print statement:
            print(f"CRITICAL DEBUG: Selected Student ID is: {student_id_for_filter}")
            courses = CourseMember.objects.filter(
                student__id=current_student.id
            ).select_related('course', 'course__subject')

            initial_list = []
            
            # 2. Check for ANY existing Report Card for this student to pre-fill grades.
            #    (If the user selected a student, we check if they have *any* saved report card)
            #    NOTE: This might pull grades from a different period if the user is reusing the wizard 
            #    for different purposes, but it adheres to the "just iterate by student" instruction.
            existing_rc = StudentReportcard.objects.filter(
                student=current_student,
            ).first() 

            # 3. Build the list of dicts for the FormSet
            for member in courses:
                # if not member.course.subject:
                #     continue
                print(f"DEBUG: Processing Course: {member.course.id}. Subject status: {member.course.subject}")
                
                row_data = {
                    'subject': member.course.subject.id, 
                }

                # If an existing Report Card was found, look for the individual Grade records linked to it
                if existing_rc:
                    # CRITICAL FILTER: Look for the grade record attached to this specific Reportcard AND Subject
                    existing_grade = ReportcardGrade.objects.filter(
                        reportcard=existing_rc, 
                        subject=member.course.subject 
                    ).first() 

                    if existing_grade:
                        row_data['final_score'] = existing_grade.final_score
                        row_data['final_grade'] = existing_grade.final_grade
                        row_data['teacher_notes'] = existing_grade.teacher_notes
                
                initial_list.append(row_data)
            
            return initial_list
        
        return initial
    
    def get_form_kwargs(self, step):
        kwargs = super().get_form_kwargs(step)
    
    # For Step 1 (FormSet), pass filtered Subject queryset based on student's courses
        if step == '1':
            step0_data = self.get_cleaned_data_for_step('0')
            if step0_data and 'student' in step0_data:
                current_student = step0_data['student']
            
            # Get all course memberships for this student
                course_members = CourseMember.objects.filter(
                    student=current_student
                ).select_related('course', 'course__subject')
            
            # Extract subject IDs from those memberships
                subject_ids = [member.course.subject.id for member in course_members if member.course and member.course.subject]
            
            # Get Subject objects
                subjects = Subject.objects.filter(id__in=subject_ids).distinct()
            
            # Pass the queryset to the formset
                kwargs['form_kwargs'] = {'subject_queryset': subjects}
    
        return kwargs

    def get_context_data(self, form, **kwargs):
        context = super().get_context_data(form=form, **kwargs)
        
        # Add student name to context for display in the header
        if self.steps.current == '1':
            data_step0 = self.get_cleaned_data_for_step('0')
            if data_step0:
                context['selected_student'] = data_step0.get('student')
            # context['selected_period'] = data_step0.get('period')
        
        return context

    def done(self, form_list, **kwargs):
        # Ambil data dari form yang sudah divalidasi
        form_data_0 = form_list[0].cleaned_data # GradeEntry
        formset_data_1 = form_list[1] # AssignmentDetailFormSet (ini formset object)

        # 1. Simpan GradeEntry (jika masih diperlukan sebagai log)
        # grade_entry_instance = form_list[0].save()

        # 2. Buat dan Simpan AssignmentHead
        # Kita gabungkan data dari Step 0 dan Step 1
        student_reportcard = StudentReportcard(
            academic_year=form_data_0['academic_year'],
            period=form_data_0['period'],
            is_mid=form_data_0['is_mid'],
            level=form_data_0['level'],
            student=form_data_0['student']
        )
        student_reportcard.save()

        # 3. Simpan AssignmentDetail (Looping FormSet)
        details_to_create = []
        
        print("\n--- DEBUG: Starting FormSet Loop ---")
        
        # NOTE: formset_data_1 is the formset instance itself
        formset = form_list[1]
        
        for i, form in enumerate(formset.forms): # Use formset.forms for clarity
            
            # Re-validate the form here to force errors to populate the form object
            is_valid = form.is_valid()
            
            print(f"DEBUG: Form Index {i}: Valid? {is_valid}")

            if is_valid and form.cleaned_data:
                # Print the data to confirm required fields are present
                print(f"DEBUG: Form {i} Cleaned Data: {form.cleaned_data}")

                # Extract the subject from this form's cleaned_data
                subject_obj = form.cleaned_data.get('subject')
                
                # Check if the subject object is None
                if not subject_obj:
                    print(f"!!! CRITICAL FAIL: Form {i} cleaned_data['subject'] is missing or None.")
                    continue

                detail = form.save(commit=False)
                detail.reportcard = student_reportcard
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
            
        return render(self.request, "partials/gradebook/finished_screen.html")