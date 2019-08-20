# Planning Center Import Part One

## Goal
Write up a script that can filter out all the unnecessary junk from the FellowshipOne Export and format it cleanly for Planning Center
## Before you start
Make sure you review these process:
### To get going
1. `git clone` the repository
2. Create a new branch named `development` -- `git branch development`
3. `git checkout` your new branch
4. `git commit` frequently!!!! 
*It's always good practice to commit after every few lines of code. It makes it easier to backtrack and fix a problem if necessary*
5. When you are done for the day, make sure to `git push` your `development` branch so that any changes you made recently are stored in a remote place

### When you file like you're ready
1. `git push` your final commits to `development`
2. Log onto github and create a new pull request. I'll take a look at your code, maybe drop some comments about what should be fixed. If it's good, we'll merge to master. If not, you head back, make the right changes and then `git push` for review again
## Usage

    $ python people_f1_to_pco.py -i INPUT_FILE -o OUTPUT_FILE
      Fellowship One to Planning Center Converter
  
      Options:
      -i INPUT_FILE 	  the path of the file to read from
      -o OUTPUT_FILE      the path of the file to write to

## The Conversion
I was doing some digging around FellowshipOne and was able to export people information about every person who has ever been put into there. Unfortunately, there a ton of useless columns that came out of this script. As it stands here are the columns that are in the CSV attached:

> Textbox575, Textbox139, Textbox145, Textbox37, Textbox411, Textbox172, Textbox230, Textbox108, Textbox146, Textbox49, Textbox147, Textbox106, Textbox151, Textbox126, Textbox154, Textbox127, Textbox204, Textbox209, Textbox157, Textbox131, Textbox158, Textbox168, Textbox161, Textbox239, Textbox603, Textbox103, Textbox44, Textbox258, Textbox104, Textbox95, Textbox469, Textbox77, Textbox114, Textbox175, Textbox178, Textbox181, Textbox184, Textbox187, Textbox190, Textbox193, Textbox116, Textbox117, Textbox118, Textbox119, Textbox120, Textbox196, Textbox86, Textbox3, Textbox205, Textbox206, Textbox207, Textbox210, Textbox222, Textbox219, Textbox216, Textbox213, Textbox231, Textbox228, Textbox225, Textbox234, Textbox237, Textbox21, Textbox240, Textbox128, Textbox1, Textbox452, Textbox192, Textbox138, Textbox130, Textbox80, Textbox73, Textbox26, Textbox15, Textbox7, Textbox33, Textbox39, Textbox48, Textbox57, Textbox52, Textbox71, Textbox76, Textbox89, Textbox94, Textbox2, Textbox25, Textbox6, address_type_name, Textbox132, Textbox134, Textbox180, Textbox135, Textbox32, Textbox136, Textbox84, Textbox137, Textbox109, Textbox99, Textbox22, address_type_name2, Textbox129, Textbox143, Textbox155, Textbox169, Textbox47, Textbox162, Textbox148, Textbox201, Textbox218, Textbox242, Textbox9, Textbox24, Textbox140, Textbox141, Textbox150, Textbox121, Textbox112, Textbox101, Textbox152, Textbox153, Textbox212, Textbox195, Textbox177, Textbox159, Textbox160, Textbox407, Textbox443, Textbox388, Textbox427, Textbox422, Textbox447, Textbox417, Textbox173, Textbox174, Textbox437, Textbox268, Textbox271, Textbox82, Textbox111, attribute_name2, Textbox382, Textbox367, Textbox324, Textbox317, Textbox75, Textbox310, Textbox401, Textbox305, Textbox307, Textbox385, **Individual_ID**, Old_Individual_ID, member_env_code, bar_code, weblink_id, Individual_Title, Full_Name, **Last_Name**, **First_Name**, Former_Name, **Household_Position1**, **gender**, **Marital_Status1**, ***age***, **date_of_birth**, dob_no_year, Status_Group, **Status_Name**, **Sub_Status1**, Status_Date1, Status_Comment, Tag_Comment, In_Directory, unsubscribed, Former_Church1, former_denomination, School_Type, School, employer, occupation, Occupation_Description1, group_membership_list, First_Record_Date, Last_Update_Date, last_attend_date, last_attend_event, last_rlc, last_contact_date, **Household_ID**, Household_Name, Household_Last_Name, Household_First_Name, Textbox233, Textbox35, children, child_attend, siblings, parent_name, parent_dob, parent_dob1, parent_status, parent_substatus, parent_first_record, parent_phone, head_phone, spouse_phone, parent_email, head_email, spouse_email, household_preferred_phone, household_preferred_email, AddressID, full_address, **street_address**, **City**, county, **State_Province**, postal_area, Postal_Code, **postal_code_short**, country, address_comment, usps_verified, AddressID2, full_address2, street_address2, city2, county2, st_province2, postal_area2, postal_code2, postal_code_short2, country2, address_comment2, usps_verified2, last_gift_date, last_gift_amount, preferred_phone, all_phones, **home_phone**, **mobile_phone**, work_phone, emergency_phone, **preferred_email**, all_emails, home_email, InFellowship_email, personal_email, social_media, Web_Address, Individual_Count, Adult_Count, Child_Count, Household_Count, HH_Member_Count, HH_Adult_Count, HH_Child_Count, Participant_Assignment_Count, Staff_Assignment_Count, Average_Age, attribute_group, attribute_name, attr_created_date, attr_start_date, attr_end_date, attr_pastor_staff, attr_staff_dept, attr_comment, all_attributes, all_attributes_by_group, attribute_name3, attr_created_date2, attr_start_date2, attr_end_date2, attr_pastor_staff2, attr_staff_dept2, attr_comment2, attr_group_name, attr_created_date3, attr_start_date3, attr_end_date3, attr_pastor_staff3, attr_staff_dept3, attr_comment3, all_requirements, requirement_name, req_status, req_date, req_portal_user, req_has_doc, req_date2, req_status2, req_portal_user2, req_has_doc2

All of the **bold** colums are important and should be remembered for later.

As you can see, most of the other columns are useless. Your task is to translate the important columns from this FellowshipOne file into a nice clean Planning Center file. Use the following mapping:
| FellowshipOne Field | Planning Center Field | Format |
|--|--|--|
| Individual_ID | FellowshipOne ID | Any Text |
| Last_Name | Last Name | Any Text |
| First_Name | First Name | Any Text |
| gender | Gender | M/F *OR* Male/Female |
| Marital_Status1 | Marital Status | Single, Married, Widowed |
| *age* | Grade | -1 to 12 (where -1 is Pre-K, 0 is Kindergarten). <br>*Age should be used to make an educated guess about grade* |
| date_of_birth | Birthdate | MM/DD/YYYY |
| Household_ID | Household ID | Any Text |
| street_address | Home Address Street Line 1 | Any Text |
| City | Home Address City | Any Text |
| State_Province | Home Address State | abbreviation or full name |
| postal_code_short | Home Address Zip Code | Any Text |
| home_phone | Home Phone Number | any length, with or without dashes |
| mobile_phone | Mobile Phone Number | any length, with or without dashes |
| preferred_email | Home Email | Any Text |
| Status_Name | Membership<br>OR<BR>Status | One of the following: <br>- Dream Team Member<br>- Growth Track Graduate<br>- Regular Attender<br>- Staff<br>*Status is set to Inactive if the Status_Name is Inactive* |
| Sub_Status1 | Campus | Must match campus names _exactly_: <br> - Christ Tabernalce // Glendale <br>- Christ Tabernacle // Bushwick <br>
| Household_Position1 | Household Primary Contact | TRUE if Household_Position1 == Head, blank otherwise |

## Things to look out for

This is **not** an exhaustive list of the items to ignore, but here are some that I found upon first glance:
- Last Names with length <= 1 should be removed
- Grade - Kids ages 2 and under should not be given a grade
- Sub_Status1 --> Campus - CTB English will map to CTG