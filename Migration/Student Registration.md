# Student Registration

**Status:** Implemented. The SchoolHub Student Registration create wizard and dynamic field-selected edit workflow are complete in the application.

## 1. Feature Description

Student Registration is a staff-operated, multi-page process for creating an admitted student, distinct from the existing Enrollment Request feature, which creates a prospective applicant. The supplied ASP captures identity and login details, family and contact information, admission and class assignment, extracurricular information, and activities; final submission writes a student and related records.

The legacy source is the evidence for observed behavior below, not proof that all supplied files belong to one working production route. The configured SchoolHub SQL Server catalog was inspected read-only for schema and object definitions. The supplied database changes script does not define the student schema. No student records were inspected.

## 2. Purpose

Give authorized school staff a way to register an admitted student, assign their class and section, record family and contact details, and initialize the related activity, contribution, and accounting records needed by other school functions.

## Student Registration - Edit Functionality

### Edit feature description

The edit feature is a staff-operated continuation of Student Registration. It starts from a searchable student register, identifies an existing student by `student_id`, loads values from `students` and related tables, allows staff to update selected data, asks for confirmation, and writes the changes atomically.

The database-change requirements state that a student has more than 50 editable fields and staff should select only the fields that need editing. Therefore, the approved target design must separate **student identification** from **field selection**: Scholar number and student name remain visible in every edit field or field group, while only the chosen fields are presented for editing.

The legacy edit implementation uses a full wizard (`studentreg1_edit.asp` through `studentreg6_edit.asp` and `StudentregActivity.asp`) and a final yes/no confirmation. The full-wizard behavior can remain as a fallback or secondary mode, but it must not replace the dynamic field-selection requirement.

### Edit purpose

- Correct or maintain an already registered student's record.
- Reduce the risk and data-entry burden caused by exposing all legacy fields for every edit.
- Preserve the student's identity and avoid replacing or duplicating the registration account.
- Synchronize related club, activity, contribution and audit records when those fields are changed.
- Reuse the existing SchoolHub authorization, navigation, validation, review and action patterns.

### What the edit feature does

1. Staff opens the Student Registration register.
2. Staff searches for a student by name, scholar number, class, father/mother name or other supported index fields.
3. The register lists matching students in pages of 10 in the legacy behavior, showing name, scholar number, class/section, father, mother, hostel, status and edit action.
4. Staff chooses Edit for a student.
5. The system loads the selected student and keeps Scholar number and name as read-only identification context.
6. Staff chooses one or more edit field groups or individual fields.
7. The system renders only the selected fields plus their dependent fields and lookups.
8. Back/continue or Cancel preserves or discards unsaved session/draft state according to the approved behavior.
9. A review page shows the original and proposed values for changed fields.
10. Confirm performs an atomic update of the approved student and related rows.
11. The system records an audit/update entry and returns to the register or review state with a success or failure message.

### Edit business logic, rules and validations

- Scholar number is a read-only identifier in edit mode. The legacy page displays and submits it, but this migration should prevent changing it through the ordinary edit form.
- Student name is read-only context in the edit view and should not be edited unless a named identity field group is deliberately selected.
- The existing `student_id` is the record key. Never infer the update target by name or scholar number alone.
- If identity fields are editable, validate first name, date of birth, sex, nationality and religion consistently with registration rules.
- Login ID can remain read-only unless explicit login-management approval is given. If edited, check uniqueness against `students.loginname` and show the existing account relationship clearly.
- Password is not a regular student edit field. Do not decrypt or repopulate legacy passwords. SchoolHub credential changes belong in Credential Manager or a separately approved password flow.
- Load `T_SwimmingPool_Contribution` for the student. Updating the contribution field requires updating or replacing the existing contribution row; preserve contributor and timestamp rules.
- Replace selected student's `Student_Activity` rows only when activity interests are changed. Preserve the student, batch/year, class and section on newly inserted rows.
- Club choices are distinct, in ranked preference order and selected from clubs eligible for the student's class through `T_Class_Club`.
- Activity choices are optional in the current SchoolHub implementation unless requirements are revised. Selected IDs must exist in `T_Activity_Master` and duplicate IDs must not create duplicate rows.
- When class or section changes, dependent section choices must reload and the existing section must remain valid for the selected class.
- Admission date, category, rebate, contribution amount and numeric fields must use server-side validation.
- Sibling scholar numbers should resolve through `V_Students`; unresolved values must not silently create a false sibling relationship.
- The legacy nine category flags (`SC`, `OB`, `BR`, `GS`, `NR`, `SIS`, `WD`, `DS`, `RTE`) must be Y/N values. `WD` can mark the student inactive only if approved; it must not be inferred by accident.
- The legacy submit block has a defect in the house-category condition because `class <> 1 OR class <> 2 OR class <> 3` is always true. The migration must use an explicitly approved class exclusion rule.
- The legacy full update writes several legacy fields, but it comments out password updates. SchoolHub must not copy the legacy encryption behavior blindly.
- The legacy full submit deletes and reinserts `Student_Activity`, replaces the swimming contribution row and inserts `T_Student_Update_Details`. It does not wrap all operations in one explicit database transaction. The migration should update atomically and roll back on failure.
- The legacy edit clears a broad set of session variables and, in page 1, deletes unbound `student_schools` rows globally. The migration must never use this behavior; drafts must be user/session scoped and previous-school cleanup must target the selected student only.
- Previous-school editing remains out of the core approval scope unless it is explicitly selected. The legacy `studentreg4_edit.asp` page is separate and not part of the active wizard default.

### Edit front-end elements and rules

| Edit area | Elements | Rules |
| --- | --- | --- |
| Student register | Search field, 10-row paginated table, student name, scholar number, class/section, father, mother, hostel, status and pencil Edit action | Search by name or supported fields; retain search/page parameters after returning; edit icon is restricted by menu access |
| Edit entry | Student identity banner/card | Read-only Scholar number and name; show selected `student_id` internally only |
| Field selector | Grouped checkboxes or selector for field groups/individual fields | Default to no fields or show recently used groups; selected fields appear below; identity fields remain pinned context |
| Identity fields | First/last name, DOB, sex, nationality, religion | Only when selected; DOB is before today; required fields are server validated |
| Contact and guardian | Address lines, city, state, country, postal code, phone, email, guardian fields | Same-address copy is conditional; communication address becomes required only when it differs |
| Parent and family | Father/mother names, professions, occupations, phone/email; sibling rows; alumni rows | Sibling scholar lookups populate name/class/section; alumni/year values remain validated text/years |
| Admission | Class, section, admission date, registration number, hostel, category, rebate, IP and swimming values | Section reload follows class; registration number and numeric fields are validated; category flags remain Y/N |
| Extra-curricular | Achievements, hobbies, special interests, other information | Optional textareas with database-length limits |
| Clubs and activities | Three ranked club selectors and activity checkboxes | Clubs are class-eligible, distinct and preference ordered; activity IDs are valid and checked values restore correctly |
| Review | Original value, proposed value and change status | Only changed fields are submitted; Cancel and Back do not commit; final confirmation is required |

The proposed edit page should not simply render all legacy controls. It should first offer field groups such as Identity, Contact, Father/Guardian, Mother/Family, Admission, Extracurricular and Activities. Staff may select one group or individual fields inside that group. Scholar number and name appear as read-only context in every resulting edit panel.

### Edit database tables and usage

| Table/view | Edit usage |
| --- | --- |
| `students` | Authoritative student record. `student_id` is the update key. Scholar number, class, section, admission, identity, family, address, category, club and extracurricular fields come from this table. It has no unique login/scholar-number index in the inspected catalog. |
| `V_Students` | Search/list and sibling lookups. It derives the display name and joins class/section and several lookup tables; missing joined values can omit or invalidate search results. Do not expose passwords from this view. |
| `T_Class_Sections` | Dependent section choices for the selected class. |
| `T_Activity_Master` | Valid activity IDs/names for activity-interest checkboxes. |
| `Student_Activity` | Replaced only for the target student when activity selections change. Batch is academic year, with class and section stored per row. |
| `T_Club_Master`, `T_Class_Club` | Club choices filtered for the student's selected class. Club preferences are stored in `students.Club1`-`Club3`. |
| `T_SwimmingPool_Contribution` | One contribution row for the target student. Update or replace only when contribution fields are selected. |
| `T_Student_Update_Details` | Audit row for each successful edit: student, update date/time, credential user ID and IP address. |
| `T_House_Category` | Recalculate house category only under an approved age/class rule. |
| `T_Nationality_Master`, `T_Religion_Master`, `T_State_Master`, `T_Country_Master`, `T_Proffession_Master`, `T_Student_Category` | Dropdown lookups for selected edit fields. |
| `student_schools` | Not edited in the core dynamic edit flow unless previous-school editing is approved explicitly. The legacy page deletes old rows and writes ten optional rows, but no proper constraints protect the relationship. |

### Edit views, procedures and triggers

- `dbo.V_Students` is the legacy read view used to search and identify students. It derives `name`, joins class/section and lookup tables, and filters active records from year greater than 2013. The edit loader should use `students` by `student_id` for authoritative update values and use `V_Students` only for search and sibling lookups.
- No registration/staff edit stored procedure is called by the supplied ASP edit files.
- A direct write to `T_SwimmingPool_Contribution` triggers `Trig_Insert_To_Contribution_History` on insert and `Trig_Update_Contribution_History` on delete. This is still a database side effect and must remain in the transaction plan.
- `T_Student_Update_Details` is not a trigger-based audit table in the supplied flow; the submit page inserts it explicitly.
- `dbo.tr_InsertCostCenter` is only relevant to new student inserts, not ordinary updates. Do not rerun create-side accounting logic during edit unless a field change is approved to do so.

### Edit wireframe

```text
DESKTOP - SELECT STUDENT
+----------------------+----------------------------------------------------------+
| SchoolHub            | Workspace > Students > Student Registration              |
|                      +----------------------------------------------------------+
| Students             | Student registrations               [New registration] |
|   Registration       | [ Search name or scholar no.          ] [Search]        |
|                      | 10 results / page                                        |
|                      | STUDENT | SCHOLAR | CLASS | FATHER | MOTHER | STATUS |  |
|                      | Asha X  | 1234    | 5-A   | ...    | ...   | Active | [p]|
+----------------------+----------------------------------------------------------+

DESKTOP - CHOOSE FIELDS
+----------------------+----------------------------------------------------------+
| Edit registration    | Scholar no. 1234  | Student  ASHA SHARMA [read-only]   |
|                      +----------------------------------------------------------+
| Field groups         | Identity                            | [Date of birth]|
| [x] Identity         | First name [____________]           | [Sex          ]|
| [ ] Contact          | Last name  [____________]           | [Nationality ]|
| [ ] Father/Guardian  |                                       [Religion     ]|
| [ ] Mother/Family    |                              [Cancel] [Review changes]|
| [ ] Admission        |                                                          |
| [ ] Extracurricular  |                                                          |
| [ ] Clubs/Activities |                                                          |
| [ ] Previous schools |                                                          |
+----------------------+----------------------------------------------------------+

DESKTOP - REVIEW AND CONFIRM
+----------------------+----------------------------------------------------------+
| Final edit review    | SCHOLAR 1234 | ASHA SHARMA                              |
|                      | FIELD            ORIGINAL       CHANGED                 |
|                      | First name       Asha          ASHA                     |
|                      | Class            5-A           6-A                     |
|                      | Swimming status  N             Y                       |
|                      |                                                          |
|                      | [Back]                             [Cancel] [Confirm]   |
+----------------------+----------------------------------------------------------+

MOBILE
+--------------------------------+
| < Student registrations        |
| Scholar no. 1234               |
| ASHA SHARMA                     |
| Edit fields                     |
| [ ] Identity                    |
| [ ] Contact                     |
| [ ] Father / Guardian           |
| [ ] Mother / Family             |
| [ ] Admission                   |
| [ ] Extracurricular             |
| [ ] Clubs / Activities          |
| [Cancel]       [Continue]       |
+--------------------------------+
```

The field selector is the preferred edit experience. The legacy 1-6 full wizard is retained as an optional **Edit all fields** mode only if staff require it and approval is given explicitly.

### Edit implementation boundaries for approval

1. Which field groups and individual fields are editable for normal staff users?
2. Is the dynamic selector mandatory, and can staff combine fields across multiple groups in one edit?
3. Should Scholar number and name always remain read-only, or can authorized administrators edit the name and number?
4. Is login ID/password editing included, or handled only through Credential Manager?
5. Which fields require before/after audit values beyond `T_Student_Update_Details`?
6. Is `Student_Activity` replacement and swimming contribution replacement always performed, or only when selected fields change?
7. Is previous-school history part of edit scope?
8. Are page 6/house number/admission-category fields required beyond the current wizard, or should page 3 admission fields remain authoritative?
9. What happens to `WD`, class changes and house-category recalculation?
10. Confirm the target database and authorization for a transaction and audit update in production.

## 3. What the Feature Does

### Observed navigation

| Source | Behavior and next destination |
| --- | --- |
| `studentreg1_add.asp` | Personal identification and initial student login; checks for existing login and scholar number, then goes to page 2. `Clear=1` clears registration session values and deletes all `student_schools` rows with a null student ID. |
| `studentreg2_add.asp` | Father's details, permanent and communication addresses, guardian and emergency contact. Next goes to page 3; Previous goes to page 1. |
| `studentreg3_add.asp` | Mother, siblings, alumni relationships, admission, class, categories and swimming contribution. Next goes directly to page 5; Previous goes to page 2. |
| `studentreg4_add.asp` | Optional ten-row previous-school form; Next saves temporary rows and goes to page 5. No incoming link from page 3 is present. |
| `studentreg5_add.asp` | Four optional extracurricular text areas. Previous goes to page 3; Next goes to `StudentregActivity.asp`. Its commented-out redirect points to page 6. |
| `StudentregActivity.asp` | Three ranked CCA club choices and activity-interest checkboxes. Next stores the choices and goes to confirmation; Previous stores them and goes to page 5. |
| `studentreg6_add.asp` | Alternative completion form with admission details and house-number check; Submit goes to confirmation, Previous goes to page 3. No supplied active page links to it. |
| `studentreg_confirm.asp` | Asks Yes/No; Yes redirects to submit, No returns to the HTTP referrer saved in session. It does not show a data summary. |
| `studentreg_submit.asp` | Rechecks login and scholar number, inserts the student, activities and swimming contribution, attaches staged school rows, clears session values, and displays success. |

**Connected route:** page 1 -> page 2 -> page 3 -> page 5 -> activity/club choices -> confirmation -> submit. Pages 4 and 6 are not linked by this route; whether they are used elsewhere remains unconfirmed. The activity page assigns the three club selections to `Club1`-`Club3` and the submitted `Ch` checkbox values to `vChValue`.

### Other supplied variants

- `studentreg4_addprev.asp` is a previous-school variant using full dates, unlike page 4's years; its form posts to `studentreg4_add.asp`. The live `student_schools` year columns are integers, so full-date compatibility is unconfirmed.
- `studentreg6_addprev.asp` is a completion variant with academic year, boarding categories, roll number, bus number and informational class/section capacity counts. It posts to `studentreg6_add.asp`; its previous action points to page 5. The roll generator is present but no submitted roll or bus value is written by the supplied submit handler. Capacity is displayed, not enforced.
- `studentreg6_add_somepart.asp` is a standalone commented fragment showing capacity and class age-range information and an over-age warning. It is not included in the active page 6 supplied; it does not establish an enforced rule.
- `studentreg7_add.asp` is an `/npt/` qualification form with up to ten board, year, qualification, division and percentage rows. It requires at least one row and, for entered rows, validates numeric percentage greater than 0 and at most 100; year blur checks four digits and current year minus 35 through current year. Its default division has a nonempty value, so the blank-division check does not reject the placeholder. It writes columns absent from the live `student_schools` schema and uses `system_registry` for a different temporary key. It goes to page 8, but no supplied current page links to it.
- `studentreg8_add.asp` is an `/npt/` form for hobbies, specific problems, additional information and document checkboxes; Next goes to page 9, Previous to page 7. It displays documents from `Student_Documents` but collects IDs from `T_Documents`, which may not match. These document tables were not found in the configured database. The supplied submit handler does not save these document/problem session values.
- `studentreg9_add.asp` has admission type, generated roll, bus and comments; Next goes to confirmation, Previous to page 5. Its JavaScript checks a nonexistent batch input, potentially preventing navigation, and the supplied submit handler does not write its admission type, roll or bus values. No active current page links to page 7.

## 4. Business Logic, Rules and Validations

### Identity and access

- Page 1 requires login ID, password and matching confirmation, a numeric scholar number, first name, date of birth, sex, nationality and religion in JavaScript. Last name is optional. Its JavaScript `trim` removes every space, not merely leading and trailing spaces; this affects blank checks and password comparison. Date of birth must parse as `dd-MON-YYYY` and precede today.
- Scholar number is suggested using `MAX(ScholarNo) + 1`; the field is editable. An empty table gives a null suggestion. This is not a concurrency-safe reservation. Login and scholar number are checked against `students` both on page 1 and at submit, but checks and insert are not atomic.
- Page 1 includes `LoginConnect.asp`, which does not itself enforce the session check. Most subsequent pages include `DbConnect.asp`, which redirects when `Session("userid")` is blank. The supplied pages do not invoke its `CheckRights` menu authorization routine. New access should use the existing SchoolHub menu authorization.
- The submit handler copies the student login to `parentlogin` and writes the same legacy `encrypt` output to student and parent passwords. The encryption include and consumers are not supplied. The live schema requires all four credential columns. Password compatibility with production student/parent login must be resolved; do not assume Django password hashes are accepted by the legacy consumers or store plaintext in a new draft.

### Contact, family and admission

- Page 2's client script checks father's name and the free-text occupation, plus permanent address line 1, city, state and country. If the copy-address checkbox is unchecked, it also checks those communication fields. When checked, JavaScript copies address, city, state, country, postal code and phone; unchecking clears them. The checkbox's session state is read but not set on this page. Postal numeric checks are commented out; guardian, email and phone fields are optional in the active checks.
- The father occupation and sub-occupation text controls share `txtFatherOccupation`; the profession dropdown is stored separately and only overwritten when nonempty. The father sub-occupation(1) has its own field. The `T_SubProfession_Master` helper is defined but not called by visible controls.
- Page 3 requires mother name, section, class, admission date, outside-hostel choice and student category in client checks; rebate must be numeric, with blank defaulting to zero. The intended registration-number check calls `trim` on a Boolean, so it is defective and may throw instead of reliably enforcing the field. Page 3 derives admission month and academic year from the admission date using VBScript `Month` and `Year`, including on Previous or class-change posts; invalid or missing dates can fail server-side.
- Class selection reloads sections from `T_Class_Sections`; IDs 14 and 15 display a With IP/Without IP choice. The code resets `rclass` at page entry and redirects for any nonempty control value before the later `ClassChange` block, so restoration and conditional-field behavior are unreliable. Class and section are foreign-key constrained in the live schema.
- Four sibling rows (two brothers, two sisters) accept scholar number; blur submits and queries `V_Students`, filling name, class ID and section name. A miss puts an error message into the name field, and submitted values can later overwrite lookup results. No validated relationship or sibling ID is stored.
- Nine independent flags `NR`, `SC`, `BR`, `SIS`, `WD`, `OB`, `GS`, `DS`, `RTE` are saved as `Y`/`N`; the source does not define their expanded meanings or mutual exclusivity. Registration number is written to both `RegdNo` and `RegistrationNo` in ASP; **the live students table has `RegistrationNo` but no `RegdNo` column**, so this assignment can fail. The ASP uses global `On Error Resume Next` and does not check the error.
- Swimming contribution amount defaults to zero when blank; status is a Yes/No select. The supplied page does not validate amount as numeric. It inserts a contribution row even for zero, with current time and session user ID.
- Up to three alumni person/relation/year rows are displayed. Page 3 accidentally stores each person name into its relation session variable instead of the relation input. Mother's email, office and mobile are stored only in the later `ClassChange` branch, not in the normal Next/Previous branch. Session clearing omits some used variables, including `rStudentEmail`, `rFatherProfession`, `rMotherProfession` and `vChValue`, risking stale values across registrations.

### Previous schools, extracurricular and save

- Page 4 stages ten `student_schools` rows under `MAX(temp_id)+1`; blank slots also create empty rows. On revisit it deletes and reinserts that temp ID. If any row value is present, client validation requires both numeric years, school name and address and checks from year is not later than to year. A four-digit/current-minus-35-to-current-year helper exists but is **not wired to the page 4 year inputs**. Page 4 is skipped by the supplied normal page 3 and page 5 navigation.
- Page 5 stores optional achievements, hobbies, special interests and other information. Previous-school controls on that page are commented out.
- The activity page lists clubs alphabetically from `T_Club_Master` where their club type is mapped to the student's selected class in `T_Class_Club`. Choice 2 is populated only after choice 1 and excludes that club; choice 3 is populated only after choices 1 and 2 and excludes both. All three are marked mandatory, but Next and Previous perform no client- or server-side required, membership, or uniqueness validation. The third choice is incorrectly labelled "Second Choice" in the legacy UI.
- The page displays one checkbox for every row of `T_Activity_Master`, with no class or status filter in the query and no minimum/maximum selection check. Next and Previous store the checkbox form collection as a comma-separated session value; submit splits it and inserts one `Student_Activity` row per value, together with the admission year, class and section. No checked boxes can leave an empty value, yet the submit loop still attempts an insert.
- Changing a club posts the form to rebuild the dropdowns. Choices are restored from the current request, not the saved session, and activity checkboxes are rendered unchecked on every page load. Returning from confirmation or page 5, or changing a club after checking activities, can therefore lose selections. The activity page also calls `MoveFirst` on the activity recordset without checking for an empty list and closes a separate unopened recordset inside the loop; errors may be suppressed by the shared connection include.
- Submit uppercases names and many address/occupation fields, sets `status` to `Active`, `Approved` to `Y`, approval date to today, and `Approved_By` to `Session("Loginname")`. The live `Approved_By` column is numeric, so the session value must be verified. Class is also copied to `Admission_Class`; admission year to `year` and `year_Admission`.
- Age is `DateDiff("yyyy", DOB, now)`, a calendar-year boundary difference, not completed age. A house category is chosen by inclusive `FromAge <= age <= ToAge`; no ordering is specified if ranges overlap. The class exclusion test uses `class <> 1 OR class <> 2 OR class <> 3`, which is always true, so the intended exclusion is not implemented.
- After the student insert, the handler looks up the ID by login, splits `vChValue` on commas, inserts an activity for each entry, links `student_schools` by `TempQ_id`, then inserts a swimming contribution. An empty/malformed activity list or temp ID can produce invalid SQL. There is no explicit transaction and the included connection file enables `On Error Resume Next`: partial writes and even a success message after failures are possible. SQL concatenation is injection-prone. The global deletion of unlinked school rows on `Clear=1` can destroy other users' in-progress data.
- The current database has no unique index on student login or scholar number. A safe migration needs an approved, concurrency-safe uniqueness strategy compatible with external database ownership; application-only prechecks do not guarantee uniqueness.

### Alternate page 6 rules

Page 6 validates class, section, numeric year, admission date format, boarding, numeric rebate and registration/scholar/house numbers; registration and scholar numbers are numeric. It checks `students.HouseNo` for duplicates before confirmation, but the submit handler does not write `HouseNo`. Its month, year and boarding dropdowns differ from page 3. Treat these as variant behavior, not confirmed additional requirements for the active page 3 path.

## 5. Front-End Elements and Data Mapping

Required marks below distinguish intended UI rules from the defects noted above. SQL column names are as used by the submit handler; availability and type must be checked before writing.

| Group | Visible controls and behavior | Main destination |
| --- | --- | --- |
| Identity | Login, password/confirmation, editable suggested scholar number, first/last name, date picker, M/F sex select, nationality and religion selects. Next checks identity. | `students.loginname`, `password`, `parentlogin`, `parentpassword`, `ScholarNo`, `first_name`, `last_name`, `dob`, `sex`, `nationalityId`, `religionId` |
| Father and contact | Name, profession select, duplicated occupation/sub-occupation text inputs, separate sub-occupation(1), office/mobile/email. Permanent and communication address lines 1-3, city, state, country, postal code and phone; checkbox copies/clears address. Student email. | `fathers_*`, `Father_SubProfession1`, `local_address_*`, `State`, `communication_*`, `student_email` on `students` |
| Guardian | Name, relationship, phone, emergency number; address lines 1-3, city, state, country, postal code, home phone. | `guardian_*`, `emergency_number` on `students` |
| Mother and siblings | Mother name, profession select, occupation, office/mobile/email; four sibling scholar/name/class/section rows with lookup on blur. | `Mothers_*`, `brother_*`, `sister_*` on `students` |
| Admission | Category checkboxes, rebate, registration number, class and dependent section selects, conditional IP choice, admission date picker, outside-hostel Yes/No, student category, swimming amount/status. | `students` admission, category and class columns; `T_SwimmingPool_Contribution` |
| Alumni | Three rows of person name, relation and year. | `Person_Name1`-`3`, `Relation1`-`3`, `Year1`-`3` on `students` |
| Extracurricular | Achievements, hobbies, special interests and other information textareas; optional. | `students.Achievements`, `Hobbies`, `Special_Interests`, `Other_Info` |
| Clubs and activity interests | Three ranked class-eligible CCA club selects, with earlier choices excluded from later lists; one checkbox per activity. All club selects show required markers, but no validation is implemented. Selection restoration is unreliable. | `students.Club1`-`Club3`; one `Student_Activity` row per selected activity |
| Previous schools | Disconnected optional page: up to ten rows of from year, to year, school name and address. | `student_schools` |
| Final | Yes/No confirmation; success message or duplicate error. | Writes and side effects described below. |

Browser `maxlength` values are not a substitute for live schema limits: for example `students.Hobbies` is `varchar(500)`, achievements/interests/other are `nvarchar(1000)`, and `Rebate` is `varchar(10)`. Validate against the verified target schema as well as approved business requirements.

## 6. Database Tables and Usability

Names and roles below are from the ASP; availability and selected column facts were checked in the configured SQL Server. They do not prove the configured database is identical to production. External tables should not be altered without approval.

| Table | Use and schema observations |
| --- | --- |
| `students` | Main admitted-student record; identity `student_id` primary key. Login, password, parent login and parent password are non-null. Class and section have foreign keys. Only the primary key was found among unique indexes on this table; no unique login/scholar index. Many other fields are nullable. `ScholarNo` is numeric, `HouseNo` text, `Approved_By` numeric; `RegdNo` is absent. |
| `student_schools` | Legacy page 4 stages and links previous schools with nullable `Student_id`, `temp_Id`, name, integer `From_Date`/`To_date`, and address. No primary, unique, foreign-key or check constraint was found. The page 7 qualification columns and `temp_school_number` are absent. |
| `Student_Activity` | Final submit writes `StudentId`, `Batch`, `ClassId`, `SectionId`, `ActivityId`; all five are non-null numeric columns. No PK, unique, FK or check constraint was found. Activity IDs come from checked `T_Activity_Master` rows. |
| `T_Activity_Master` | Activity-interest checkbox source. `ActivityId` is identity numeric and `ActivityName` is required `varchar(50)`; the legacy page selects every row. No PK, unique, FK or check constraint was found in the inspected catalog. |
| `T_Club_Master`, `T_Class_Club`, `T_Club_Type` | `T_Club_Master` supplies club ID, name and club type; `T_Class_Club` maps class IDs to eligible club type IDs. The page filters clubs by that mapping, not by direct club-to-class rows. Both tables have foreign keys to `T_Club_Type`; the mapping also references `classes`. Club preferences are stored on `students`, not in `Student_Activity`. |
| `T_SwimmingPool_Contribution` | Contribution amount, Y/N status, student, creator and timestamp; identity `Id`. Insert trigger also writes history. No FK, unique or check constraint was found. |
| `T_House_Category` | Inclusive age ranges `FromAge`, `ToAge` determine `HouseCategoryId`; no deterministic tie-breaking in ASP. |
| `classes`, `T_Class_Sections` | Class choices and sections filtered by class. Section has identity `section_id`, required `class_id`/`section_name`, optional capacity and status. |
| `T_Nationality_Master`, `T_Religion_Master` | Nationality and religion dropdown values. |
| `T_Country_Master`, `T_State_Master` | Address choices; the legacy page loads all states and countries independently, not cascading by country. |
| `T_Proffession_Master`, `T_subProfession_Master` | Parent profession choices; subprofession helper is unused by page 2's visible controls. |
| `T_Student_Category` | Student category select, identified by `CId`. |
| `T_eIMS_Master`, `T_CostCenter`, `T_Costcenter_Details` | Accounting dependencies used by the student-insert trigger, not explicit ASP writes. |
| `T_SwimmingPool_Contribution_history` | Receives contribution history through insert/delete triggers. |
| `T_Month_Master`, `T_Boarding_Category`, `T_Admission_Category` | Helpers for alternate or commented forms. Page 6 actively uses month and boarding tables; page 3's month, boarding and admission-category helpers are not active controls. |
| `system_registry`, `T_Class_Specifications` | Used only by the disconnected qualification variant and age/capacity fragment, respectively. Their use in the current flow is unconfirmed. |
| `Student_Documents`, `T_Documents` | Referenced by disconnected page 8; not found in the configured database catalog. |

## 7. Views, Stored Procedures and Triggers

### `dbo.V_Students` (verified live definition)

Page 3 queries `Name`, `class_id` and `section_name` by `ScholarNo`. The view derives `name` as `first_name + ' ' + last_name`, includes many student/contact and lookup fields, and filters `students.year > 2013` and `status = 'Active'`. It inner-joins `classes`, `T_Curriculum_master`, `T_Class_Sections`, communication `T_State_Master` and `T_Country_Master`; missing matches exclude a student. Profession, house category, student category, hostel, religion, nationality and local state/country use left joins. Thus a scholar number in `students` may still not be found; a null name component can make the concatenated name null. The view also exposes student and parent password columns, which must not be surfaced by a new lookup.

### Stored procedures

No stored procedure is called by the supplied registration pages. A read-only catalog search of visible procedure definitions for direct `students` inserts and `student_schools` references found no matching procedure; this is not proof that no indirect or encrypted procedure exists. Other student-related procedures exist but are not called in the supplied flow.

### Relevant live triggers

- `dbo.tr_InsertCostCenter` is enabled `FOR INSERT` on `students`. It reads `LEFT(FinancialYear,4)` from `T_eIMS_Master`, takes `ScholarNo` from `inserted`, inserts an active category-1 row into `T_CostCenter`, obtains `MAX(CostCenterId)`, then adds zero-credit opening balances dated April 1 of that financial year in `T_Costcenter_Details` for account IDs 92, 156, 155, 465 and 546. It assumes a single inserted row and uses a concurrency-unsafe maximum; account setup, financial-year data and trigger behavior must be checked in the target environment. Do not create duplicate accounting rows in application code.
- Enabled `Trig_Insert_To_Contribution_History` copies inserted swimming contribution student, amount, status, creation date and creator to `T_SwimmingPool_Contribution_history`. Enabled `Trig_Update_Contribution_History`, despite its name, runs after **delete** and copies deleted values. These are database side effects, not ASP calls.

## 8. Proposed Wireframe

The following is a proposal, not an approved feature scope. Use the existing SchoolHub sidebar, header, breadcrumb, compact workspace layout and enrollment-wizard styling. Split page 3 into smaller logical steps while retaining its data. Back/Continue should preserve entries; server-side validation shows inline errors. No database-backed draft is assumed.

```text
DESKTOP
+----------------------+----------------------------------------------------------+
| SchoolHub            | Workspace > Students > Student Registration              |
|                      +----------------------------------------------------------+
| Overview             | Student Registration                    [Cancel]         |
| Students             |                                                          |
|   Enrollment Request | 01 Identity  02 Contacts  03 Family  04 Admission        |
|   Student Registration| 05 Activities  06 Review                                |
| Staff                +----------------------------------------------------------+
| ...                  | 01  Student identity                                     |
|                      | Login ID *       [_______________________________]       |
|                      | Password *       [_______________________________]       |
|                      | Confirm password * [_____________________________]       |
|                      | Scholar no. *    [_____________]                          |
|                      | First name *     [_____________]  Last name [________]    |
|                      | Date of birth *  [____ / ____ / ______]                    |
|                      | Sex *            [Select v]                                |
|                      | Nationality *    [Select v]        Religion * [Select v]  |
|                      |                                      [Continue ->]        |
+----------------------+----------------------------------------------------------+

OTHER STEPS
02 Contacts   Father | Permanent address | [ ] Same communication address
              Communication address | Student email | Guardian and emergency
03 Family     Mother | Sibling scholar lookup (up to 4) | Alumni (up to 3)
04 Admission  Class -> Section | Admission date | Registration no. | Hostel
              Student category | Category flags | Rebate | Swimming contribution
              Conditional With/Without IP for the applicable classes
05 Activities Achievements | Hobbies | Special interests | Other information
              CCA club preferences: First [Select v] Second [Select v]
              Third [Select v] (eligible clubs; no duplicate choices)
              Activity interests: [ ] Activity 1  [ ] Activity 2  [ ] ...
06 Review     Student | Login ID | Scholar no. | Class/section | Admission
              Contact/family | Categories | Contribution | Activities
              [Back]                                      [Confirm registration]

MOBILE
+----------------------------------+
| Menu  Student Registration      |
| 01 of 06  Student identity      |
| Login ID *                       |
| [______________________________] |
| Password *                       |
| [______________________________] |
| ...                              |
| [Back]                [Continue] |
+----------------------------------+
```

Proposed final confirmation displays the values being saved without revealing the password, including ranked club choices and selected activity interests. A successful save returns a clear success state; a duplicate or database failure preserves input and explains the issue. Previous-school history is not included in the main proposal because the supplied active route skips it; its inclusion remains a review decision.

## 9. Original Review Decisions and Implementation Boundaries

The following questions were recorded during analysis. The implementation choices and remaining limitations are summarized below.

1. The legacy page marks all three ranked club choices mandatory but does not enforce them; activity interests have no required marker or selection validation. Confirm the desired minimum/maximum club and activity selections, including what happens when fewer than three eligible clubs exist, and approve server-side validation and selection preservation.
2. Is the optional previous-school page part of this menu's intended production workflow despite being skipped? If yes, confirm year-only fields, maximum of ten rows and validation; approve its position in the wizard.
3. Confirm whether page 6's house number, separate admission month/year, boarding-category choices, roll, bus and comments are needed, or whether page 3's admission controls are authoritative. Clarify category abbreviation meanings and conditional IP rule.
4. Confirm the login/parent-login policy and provide the legacy encryption and authentication consumer requirements. The existing schema requires both credential pairs; a compatible secure design needs agreement before implementation.
5. Confirm whether registration should immediately mark the student active/approved, the correct numeric approval actor, the academic-year rule, age calculation and house-category exclusions. Confirm whether to correct the evident relation, mother-contact and `RegdNo` bugs rather than reproduce them.
6. Confirm the authoritative target database and permission to inspect any additional schema/dependencies. Decide how to enforce login/scholar uniqueness and handle trigger concurrency without unapproved changes to external schema. Confirm swimming contribution zero/default behavior.
7. Confirm whether Student Registration starts directly at a new form or needs a student register/list. No listing page was supplied, so the wireframe does not invent one. Confirm whether any applicant-to-student conversion is required; no link is demonstrated in these files.

Do not copy hard-coded credentials from the legacy connection files; treat them as exposed and rotate them through the appropriate administrator.

## Implementation Status

- The create wizard is implemented in SchoolHub and retains the existing registration flow.
- The edit workflow starts from the registrations register, loads the selected `student_id`, and offers grouped individual-field selection.
- Scholar number and student name remain read-only context; only selected fields are shown and submitted.
- Confirmation shows original versus changed values before an atomic partial update.
- Create-only credential creation does not run during edit; updates use `students`, related activity/contribution tables and `T_Student_Update_Details` audit records.

## 10. Source Inventory

Edit-specific sources reviewed:

- `student_view_All.asp` - searchable student register and edit link.
- `studentreg1_edit.asp` - identity, password context, scholar number and loaded student values.
- `studentreg2_edit.asp` - father, addresses, communication address, guardian and emergency fields.
- `studentreg3_edit.asp` - mother, siblings, alumni, class, section, admission, category, rebate and swimming contribution.
- `studentreg4_edit.asp` - optional previous-school edit variant.
- `studentreg5_edit.asp` - extracurricular text fields.
- `studentreg6_edit.asp` - alternate admission/completion variant.
- `StudentregActivity.asp` - club preferences and activity interests.
- `studentreg_edit_confirm.asp` - yes/no update confirmation.
- `studentreg_edit_submit.asp` - record update and related activity/contribution/audit writes.

The folder's shared source is treated as context only: edit pages include legacy database, display, date and clear-session helpers. Referenced shared files including `crypt.asp`, `dateconverter.asp`, `displaydate.asp`, `page_loading.asp`, the form wrapper and calendar resources were not supplied, so their internal behavior is not independently verified.

## 11. Review Status

Dynamic field-selected edit implementation is complete. Remaining operational items are menu access assignment, production database verification and approved test-record validation.