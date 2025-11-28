from django.contrib import admin
import decimal
from .models import Subject, Course, CourseMember, AssignmentType, Weighting, GradeEntry, PassingGrade

class SubjectAdmin(admin.ModelAdmin):
    list_display = ["subject_name", "short_name"]

class CourseMemberInLine(admin.TabularInline):
    model = CourseMember
    fields = ("is_active", "na_date", "na_reason")
    max_num = 0

class CourseAdmin(admin.ModelAdmin):
    list_display = ["short_name", "academic_year", 'get_teacher_name']
    inlines = [ CourseMemberInLine, ]
    search_fields = ["name"]

    def get_teacher_name(self, obj):
        return f"{obj.teacher.first_name} {obj.teacher.last_name}"
    get_teacher_name.short_description = "Teacher"


class CourseMemberAdmin(admin.ModelAdmin):
    list_display = ["get_course_name", "student", "is_active"]
    autocomplete_fields = ["student", "course"]
    def get_course_name(self, obj: CourseMember)->str:
        return f"{obj.course.short_name}"
    get_course_name.short_description = "Course"

class PassingGradeAdmin(admin.ModelAdmin):
    list_display = ["academic_year","subject", "level", "passing_grade"]

class AssignmentTypeAdmin(admin.ModelAdmin):
    list_display = ["short_name", "name"]

class WeightingAdmin(admin.ModelAdmin):
    list_display = ["academic_year","subject","assignment","format_percentage"]
    list_filter = ["academic_year", "subject", ]

    def format_percentage(self, obj: Weighting)->decimal:
        return obj.weight*100
    format_percentage.short_description = "Weight %"

class GradeEntryAdmin(admin.ModelAdmin):
    list_display = ("academic_year", "school_level", "course", "period", "subject", "teacher")
    def delete_queryset(self, request, queryset):
        pass

# Register your models here.
admin.site.register(Subject, SubjectAdmin)
admin.site.register(Course, CourseAdmin)
admin.site.register(CourseMember, CourseMemberAdmin)
admin.site.register(AssignmentType, AssignmentTypeAdmin)
admin.site.register(Weighting, WeightingAdmin)
admin.site.register(PassingGrade, PassingGradeAdmin)
admin.site.register(GradeEntry, GradeEntryAdmin)