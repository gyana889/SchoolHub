# Enrollment Request

**Status:** Implemented in SchoolHub for the connected pages 1-6 enrollment flow.

## 1. Feature Description

Enrollment Request is the staff-facing, multi-step workflow for entering a prospective student's pre-application. It gathers student identity, contact and guardian details, family information, prior-school history, extracurricular details, and requested enrollment information. On confirmation, the legacy system creates an applicant record and associates prior-school rows with it.

The legacy pages use an authenticated session and carry form values between pages in ASP session variables. The forms are not a public self-service registration flow in the source reviewed.

## 2. Purpose

Capture a prospective student's application and related family and school-history information in a consistent record for the school's enrollment/admissions process. The initial record is marked `Applied` by the submit handler.

## 3. What the Feature Does

The connected pages establish this flow:

1. **Personal Identification** (`applicantreg1_add.asp`): registration number, name, birth details, sex, nationality, and religion. Checks that the pre-application number is not already in `T_Applicants_New`.
2. **Communication Details** (`applicantreg2_add.asp`): permanent, communication, and guardian addresses; contact details; and two referees. A client-side checkbox copies or clears communication details from permanent details.
3. **Parent's & Family Details** (`applicantreg3_add.asp`): parent names, professions, income, education, alumni status, sibling/single-parent/special-needs indicators, sibling details, and old-boy relationship details.
4. **Previous School Details** (`applicantreg4_add.asp`): up to ten rows of school name, address, and from/to years. Rows are staged in `Applicant_Schools` using a temporary ID.
5. **Extra Curricular Activities** (`applicantreg5_add.asp`): achievements, hobbies, special interests, and other information. The old previous-school controls on this page are commented out.
6. **Application Details** (`applicantreg6_add.asp`): class applying for, registration year, private-hostel choice, and optional present-class/promotion/school details. Submit routes to confirmation.
7. **Confirmation and save** (`applicantreg_confirm.asp`, `applicantreg_submit.asp`): Yes saves; No returns to the previous page. The handler creates the applicant row, attaches staged school rows, and clears session values after commit.

**Flow caveat:** Page 5 redirects to `applicantreg_OtherSpec_add.asp`, which is not present in `Old Project Files`. Page 6's caller is therefore not verified from this folder. The implementation uses the connected pages 1-6 data set and moves from activities to application details. The `applicantreg7_add.asp` through `applicantreg10_add.asp` pages form a separate `/npt/`-based flow (qualification, survey, status/center, and payment) and are not connected to the visible pages 1-6; they are not included.

## 4. Business Logic, Rules, and Validations

### Observed rules

- The pre-application number is checked for an existing match before advancing. A match displays an “already exists” message; an unused number advances.
- Required-field checks are primarily JavaScript in the browser. The form values are stored in session variables as the user moves between pages.
- The previous-school section allows up to ten entries. If any value in a row is entered, the page requires both years, school name, and address; it checks numeric years, four digits, a year range from current year minus 35 through current year (on blur), and `from year <= to year`.
- Final confirmation presents Yes and No. Yes invokes the insert handler; No redirects to the recorded referring page.
- The applicant is assigned `Admission_status = "Applied"`. The handler also fills blank guardian state/country values with `1` and `16` respectively.

### Legacy validation behavior and inconsistencies

- Page 1 checks registration number, first and last names, DOB, birth-certificate issue date, sex, nationality, and religion. The date inputs have no effective format/range validation. The visible required markers do not exactly match the checked fields.
- Page 2 requires permanent address line 1, city, state, and country. If “Same as Above” is not checked, it also requires communication address line 1, city, state, and country. ZIP checks only reject non-numeric strings; blank ZIP values pass. The checkbox copies/clears fields in JavaScript, but its checked state is not saved with the form.
- Page 3 requires father and mother names. The father-profession check accepts either a profession dropdown value or free text. The father-post check mistakenly tests the same post field twice. Income, student category, sibling, single-parent, and special-needs fields are marked required in the HTML but are not checked by the submit JavaScript.
- Page 4 year validation is client-side only. Partial rows are rejected by JavaScript, but no equivalent server-side validation is visible. The page inserts empty staging rows for blank slots.
- Page 5 fields are optional and have no active validation.
- Page 6 checks that class and boarding choice are selected. The year input has a hard-coded default of `2011` and is not validated. The class dropdown helper used by the visible controls selects `class_id = 2`; a general class-list helper exists but is not used there. Category, exam-center, and comments controls are commented out.
- In page 1, `rChild` is looked up by matching the sex value against `T_Specification_Master.SpecificationName`; this mapping is unusual and the query result is not checked for no match.
- Persistence uses a transaction, but error handling is suspect: the handler commits before clearing/checking the error, and the later rollback check may not detect an earlier failure. Applicant ID is obtained with `MAX(applicant_id)`, which is not safe for concurrent submissions. The duplicate-number check is separate from the insert.
- The legacy source constructs SQL from request/session values in places. This is a risk, not a behavior to carry into Django; new code should use ORM/parameterized operations and server-side validation.

## 5. Front-End Elements and Rules

The legacy UI is a set of separate HTML forms with `NEXT` and `PREVIOUS` buttons; state is repopulated from session variables. Dropdown options are loaded from database reference tables. Dates use text inputs and, on some pages, a legacy calendar widget.

- **Identity:** text inputs for registration number, first/last name, DOB, issue date, place of birth, and mother tongue; sex, nationality, and religion selects.
- **Contact:** text inputs for three address lines, city, postal code, phone, fax, and email; state/country selects; neighborhood selects; “Same as Above” checkbox; two referee name/address pairs; optional guardian identity and address fields.
- **Family:** parent name, profession/sub-profession selects and free-text profession fields; income, qualification/alumni selects, phones, emails; category/sibling/single-parent/special-needs selects; up to two brother and two sister rows; two old-boy relationship rows.
- **Previous schools:** a fixed ten-row table with from year, to year, school name, and address.
- **Activities:** four multiline textareas.
- **Application:** class and hostel selects, year input, present class select, promotion date picker, present-school and address inputs.
- **Confirmation:** a confirmation question and Yes/No actions.

For the new experience, preserve the workflow and data intent, not the old table layout or browser-only validation. Proposed wireframe below uses the current SchoolHub sidebar/header/footer, breadcrumb, compact page heading, clear stage indicator, responsive field groups, and a persistent Back/Continue action area. Validation should be enforced server-side and reflected inline.

## 6. Database Tables and Usability

The table names below were verified against the configured SQL Server. The supplied `SchoolHub Database Changes.sql` does not define the applicant schema, so the live database catalog was used. `T_Applicants_New` has an identity `applicant_id`; its remaining 142 columns are nullable. `applicant_schools` has nullable `applicant_id`, `temp_id`, `school_name`, `Address`, `from_date`, and `to_date` columns and no primary key or declared foreign key. The implementation writes applicant and non-empty school-history rows in one Django transaction and does not create schema migrations for these externally managed tables.

| Table | Use in the legacy flow |
| --- | --- |
| `T_Applicants_New` | Main applicant record. Duplicate registration check, final insert, `Admission_status`, and enrollment fields. |
| `applicant_schools` | Stores up to ten prior-school rows with `school_name`, `Address`, `from_date`, `to_date`, and the final `applicant_id`. The new flow inserts linked rows in the final transaction instead of creating orphanable temporary rows. |
| `T_Nationality_Master` | Nationality choices. |
| `T_Religion_Master` | Religion choices. |
| `T_Specification_Master` | Sex lookup and neighborhood, qualifications, alumni, sibling, single-parent, and special-needs choices filtered by `criteriaId`. |
| `T_Country_Master`, `T_State_Master` | Country and state choices for permanent, communication, and guardian addresses. |
| `T_proffession_Master`, `T_proffession_SubMaster` | Parent profession and sub-profession choices (spelling as used in the ASP). |
| `T_Student_Category` | Student category/caste choices. |
| `classes` | Class labels and IDs; page 3 uses active classes for sibling details; page 6's visible class helper is fixed to class ID 2. |

Other lookup routines for `T_Boarding_Category`, `T_Admission_Category`, and `T_ExamCenter` exist on page 6, but the corresponding visible controls are commented out or otherwise unused in the active page. They are not confirmed inputs to this path.

The live `T_Applicants_New` table does not contain `BrotherSection`, `BrotherSection1`, `SisterSection`, or `SisterSection1`; these controls are omitted because their values cannot be saved to the required legacy tables. The separate `/npt/` pages reference `applicant_schools` with a different temporary key and qualification columns, `student_schools`, `system_registry`, and `survey`. Their differing column usage is evidence of a separate/older registration track, not a dependency of pages 1-6.

## 7. Views and Stored Procedures

- No stored procedure call is present in the reviewed enrollment form/submit pages and no applicant/enrollment stored procedure was found in the live database catalog.
- The live `dbo.V_Applicant_Edit_New` view selects applicant identity, class, application year/status, contact and address fields, and lookup labels. It computes `full_name` as `First_Name + ' ' + Last_name`, left-joins `classes` on `class_id`, and left-joins `T_Country_Master` and `T_State_Master` for communication-country/state labels. The Enrollment Request register reads and searches this view, ordered by descending `applicant_id`.
- The view is externally managed and is not represented by a Django migration. Applicant creation writes to `T_Applicants_New`; school-history rows write to `applicant_schools`. All lookup options are read from the legacy lookup tables listed above.

## 8. Proposed Wireframe

Desktop layout within the existing SchoolHub workspace shell. Each stage occupies the same page frame; the stage indicator and action footer remain stable. Long sections (addresses/family) scroll within the content area, with controls wrapping to one column on narrow screens.

```text
┌──────────────────────┬──────────────────────────────────────────────────────────┐
│ SchoolHub            │ Workspace  >  Students  >  Enrollment Request             │
│                      ├──────────────────────────────────────────────────────────┤
│ Overview             │ Enrollment Request                         [Save Draft*] │
│ Students             │ Create a prospective student's application               │
│   Enrollment Request ├──────────────────────────────────────────────────────────┤
│ Staff                │ 1 Student  ── 2 Contacts ── 3 Family ── 4 School History │
│ Attendance           │                         ── 5 Activities ── 6 Application  │
│ ...                  ├──────────────────────────────────────────────────────────┤
│                      │ STUDENT IDENTITY                                         │
│                      │ Registration No.* [________________]  Sex* [Select   v] │
│                      │ First name*       [________________]  Last name* [___] │
│                      │ Date of birth*    [____ / ____ / ______]               │
│                      │ Birth cert. issue [____ / ____ / ______]               │
│                      │ Place of birth     [________________]                  │
│                      │ Mother tongue      [________________]                  │
│                      │ Nationality* [Select                         v]        │
│                      │ Religion*    [Select                         v]        │
│                      ├──────────────────────────────────────────────────────────┤
│                      │ [Cancel]                         [Continue  →]           │
└──────────────────────┴──────────────────────────────────────────────────────────┘
```

The six-stage grouping consolidates the connected pages 1-6. The wizard keeps in-progress values in the signed-in Django session; there is no separate database-backed draft feature. The missing `OtherSpec` page and disconnected pages 7-10 are not implemented.

## Implementation Notes

- The workflow is staff-facing and protected by the existing Students / Enrollment Request menu access grant.
- The new page lists existing requests from `V_Applicant_Edit_New`; new records are created only after final confirmation.
- Server-side validation is used. Legacy fixed defaults such as year `2011` and forced class ID `2` are not reproduced; active classes and a user-entered four-digit registration year are used.
- The old page's guardian state/country hard-coded defaults are not written. Blank optional guardian location fields remain blank.
- Views, forms, transaction handling, templates, and navigation follow the existing Django project patterns; the legacy ASP page markup is not reused.