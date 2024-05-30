# .... 

import asyncio
import csv
import json
from playwright.async_api import async_playwright
import os
from config import bot_manual_setting, preview
from manage_json import load_json, save_json



def transform_data(data):
    transformed_data = {}
    for row in data:
        # input('press next ')
        print(row)
        if len(row)>4:
            row = row[:4]
            transformed_data[row[0]] = row[-1]


        elif len(row)>=2:

            transformed_data[row[0]] = row[-1]

        # elif len(row) ==4:
        #     transformed_data[row[0]] = row[-2]
        else:
            print(f"Ignoring row: {row}. Insufficient data.")
    return transformed_data


async def delay(seconds=0.5):
    await asyncio.sleep(seconds)


async def press_enter(page):
    await page.keyboard.press('Enter')


async def handle_warning(page, bot):
    await page.wait_for_load_state(state='networkidle')

    try:
        # Check if the warning message exists
        warning_inner_text = await page.evaluate('''() => {
            const warningMessage = document.querySelector('#failbodylabel .notification_banner.notification_banner_orange .body');
            return warningMessage ? warningMessage.innerText.trim() : null;
        }''')

        print("warning text", warning_inner_text.split('\n')[0].strip())

        if warning_inner_text.split('\n')[0].strip() != "WARNING":
            return False

        # Check if the warning message exists
        warning_exists = await page.evaluate('''() => {
            const warningMessage = document.querySelector('#failbodylabel .notification_banner.notification_banner_orange .body');
            if (warningMessage) {
                const innerText = warningMessage.innerText.trim();
                return innerText.startsWith("WARNING");
            }
            return false;
        }''')

        if warning_exists:
            await bot.message.reply_text(
                "WARNING: You have not answered all required questions. Continue? (ok/never) reply me with ok or never\n\nIf there is not POP up Please reply me with ok ",
                reply_to_message_id=bot.message.message_id)

            while True:
                state = load_json()  # Load JSON data inside the loop to get the most recent state

                await delay(1)
                if state.get("user_confirmed_proceed") == '3':  # proceed
                    new_data = {"user_confirmed_proceed": "1"}  # return value to default
                    save_json(new_data)
                    try:
                        await page.click('#failcontinueButton')
                        # await page.wait_for_load_state("domcontentloaded")
                        return True

                    except:
                        return False

                elif state.get('wizard', False):
                    await page.click('#failcontinueButton') # If wizard is true dont wait... just click..
                    await bot.message.reply_text(
                        "WIZARD: I am moving on !!! 😎 give me some sec ... ",
                        reply_to_message_id=bot.message.message_id)
                    await page.wait_for_load_state(state='networkidle')
                    return True



                elif state.get("user_confirmed_proceed") == '2':  # click no
                    new_data = {"user_confirmed_proceed": "1"}  # return value to default
                    save_json(new_data)
                    try:
                        await page.click('#failcancelButton')
                        return False
                    except:
                        return False
    except Exception as e:
        print(f"An error occurred: {e}")
        return False


async def click_next_page(update, bot, page, mode=None):
    if bot_manual_setting:
        recent_message = await bot.message.reply_text("Do you want to continue to next page? Reply with 'Yes' or 'No'",
                                                      reply_to_message_id=bot.message.message_id)

        while True:
            state = load_json()
            if state.get("user_confirmed"):
                new_data = {"user_confirmed": False}
                save_json(new_data)

                await update.edit_text("Clicking Next button.........")
                if mode == 'login':
                    await page.click("button#next")
                else:
                    await page.click("button.next")

                await asyncio.sleep(0.5)
                await page.wait_for_load_state("domcontentloaded")

                break

            await asyncio.sleep(1)

        return recent_message

    else:
        await update.edit_text("Clicking Next button.........")
        if mode == 'login':
            await page.click("button#next")
        else:
            await page.click("button.next")

        await asyncio.sleep(0.5)
        await page.wait_for_load_state("domcontentloaded")

async def login_page(update, page, data, bot=None):
    await update.edit_text("Logging in.........")
    await page.fill("#signInName", data.get("signInName", ""))
    await asyncio.sleep(1)
    await page.fill("#password", data.get("password", ""))
    await asyncio.sleep(1)





async def first_page(update, page, data):
    # Navigate to the page and wait for it to fully load
    await page.wait_for_load_state(state='networkidle')

    async def navigate_to_visa_application_page():
        await update.edit_text("Navigating to the visa application page...")
        await page.wait_for_load_state("load")
        await page.wait_for_selector('a[title="APPLY FOR A VISA"]', timeout=60000)
        await page.click('a[title="APPLY FOR A VISA"]')

    async def select_visa_type(visa_type):
        await update.edit_text("Waiting for the dropdown to appear...")
        await page.wait_for_load_state("load")
        await page.wait_for_selector('select[name="6595ea5a-e55e-ec11-8f8f-000d3ad0d7d1"]')
        await update.edit_text("Selecting the visa type...")

        if visa_type.lower() == "temporary visa":
            await page.select_option('select[name="6595ea5a-e55e-ec11-8f8f-000d3ad0d7d1"]', value="Temporary visa")
        elif visa_type.lower() == "resident visa":
            await page.select_option('select[name="6595ea5a-e55e-ec11-8f8f-000d3ad0d7d1"]', value="Resident visa")
        else:
            print("Invalid visa type specified in CSV.")

    async def handle_is_outside_nz(is_outside_nz):
        if is_outside_nz.lower() == "yes":
            await update.edit_text("Applicant is outside New Zealand. Clicking 'Yes' button...")
            await page.click('input[id="0607d49f-8f0c-ed11-b83d-00224891ea27_TRUE"]')
            await update.edit_text("Selecting visa type for applicants outside New Zealand...")
            selected_visa_type = data.get("OutsideNZVisaType", "Visitor")
            print(selected_visa_type)
            await page.select_option('select[name="89ee7dfa-90b3-eb11-8236-0022480fd66e_select"]', value=selected_visa_type.capitalize())

        elif is_outside_nz.lower() == "no":
            await update.edit_text("Applicant is inside New Zealand. Clicking 'No' button...")
            await page.click('input[id="0607d49f-8f0c-ed11-b83d-00224891ea27_FALSE"]')
        else:
            print("Invalid value for 'IsOutsideNZ' field in CSV.")

    async def handle_is_australian_pr_or_visa_waiver(is_australian_pr_or_visa_waiver):
        if is_australian_pr_or_visa_waiver.lower() == "yes":
            await update.edit_text(
                "Applicant is a citizen or permanent resident of Australia or a citizen of a visa waiver country. Clicking 'Yes' button...")
            await page.click('input[id="4710ca77-136b-eb11-a812-000d3acb9f99_TRUE"]')
        elif is_australian_pr_or_visa_waiver.lower() == "no":
            await update.edit_text(
                "Applicant is not a citizen or permanent resident of Australia or a citizen of a visa waiver country. Clicking 'No' button...")
            await page.click('input[id="4710ca77-136b-eb11-a812-000d3acb9f99_FALSE"]')

            purpose_of_visit = data.get("PurposeOfVisit", "covid-19")
            print("purpose_of_visit", purpose_of_visit)
            if purpose_of_visit.lower() in ["covid-19", "tourism or holiday", "event", "professional", "family", "private yacht or plane", "other"]:

                if purpose_of_visit.lower() == "tourism or holiday":
                    purpose_of_visit = "Tourism or Holiday"
                elif purpose_of_visit.lower() == "private yacht or plane":
                    purpose_of_visit = "Private Yacht or Plane"
                else:
                    purpose_of_visit = purpose_of_visit.capitalize()

                await update.edit_text(f"Selecting purpose of visit: {purpose_of_visit}...")
                await page.select_option('select[name="cec3f50f-9cb3-eb11-8236-0022480fd66e_select"]', value=purpose_of_visit)

                selected_option = data.get("VisitOption", "")
                await page.select_option('select[name="8aa075eb-9cb3-eb11-8236-0022480fd66e_select"]', value=selected_option.capitalize())

            else:
                print("Invalid purpose of visit specified in CSV.")

        else:
            print("Invalid value for 'IsAustralianPRorVisaWaiver' field in CSV.")

    # Call the nested functions
    await navigate_to_visa_application_page()

    visa_type = data.get("VisaType", "")
    await select_visa_type(visa_type)

    is_outside_nz = data.get("IsOutsideNZ", "")
    await handle_is_outside_nz(is_outside_nz)

    is_australian_pr_or_visa_waiver = data.get("IsAustralianPRorVisaWaiver", "")
    await handle_is_australian_pr_or_visa_waiver(is_australian_pr_or_visa_waiver)


async def second_page(update, page, data):
    # Navigate to the page and wait for it to fully load
    await page.wait_for_load_state(state='networkidle')

    await update.edit_text("Navigating to the second page...")

    async def click_continue_button(page):
        await page.click('td[data-attribute="mcs_resumeurl"] a.btn-primary')
        await page.wait_for_load_state("domcontentloaded")

    await click_continue_button(page)
    await update.edit_text("Clicked the 'Continue' button on the second page.")





async def third_page(update, page, data):
    # Navigate to the page and wait for it to fully load
    # await page.wait_for_load_state(state='domcontentloaded')
    await page.wait_for_load_state(state='networkidle',timeout=120000)

    async def click_radio_button():

        is_mononym = data.get("IsMononym", "")  # get data from csv

        if is_mononym.lower() == "yes":
            # await page.wait_for_load_state(timeout=120000)
            await update.edit_text("Clicking 'Yes' for mononym...")
            await page.click('input[id="f40bafb2-b870-eb11-a812-000d3acba81e_TRUE"]')
            # If yes
            user_name = data.get("UserName", "")
            await update.edit_text("Entering name...")
            await page.fill('input[name="7d064b39-b970-eb11-a812-000d3acba81e"]', user_name)

        elif is_mononym.lower() == "no":
            await update.edit_text("Clicking 'No' for non-mononym...")
            await page.click('input[id="f40bafb2-b870-eb11-a812-000d3acba81e_FALSE"]')
            # If no
            await update.edit_text("Entering given/first name...")
            given_name = data.get("GivenName", "")
            await page.fill('input[name="42519f4b-b970-eb11-a812-000d3acba81e"]', given_name)
            await update.edit_text("Entering middle name...")
            middle_name = data.get("MiddleName", "")
            await page.fill('input[name="d452ba5d-b970-eb11-a812-000d3acba81e"]', middle_name)
            await update.edit_text("Entering surname/family name...")
            surname = data.get("Surname", "")
            await page.fill('input[name="1784ec76-f96f-eb11-a812-000d3acba81e"]', surname)

        else:
            print("Invalid value for 'IsMononym' field in CSV.")

    async def handle_other_names():
        # Code to handle the radio button for "Have you ever used any other names?"
        # This code block is separate from click_radio_button()
        # You can add your code here
        is_other_names = data.get("OtherNames", "")  # Assuming "OtherNames" is the key for the yes/no value
        if is_other_names.lower() == "yes":


            # Perform actions if yes
            await update.edit_text("You have used other names. Entering details...")
            # Click on the radio button for "Yes"

            await delay()

            await page.click('input[id="315e92cb-b970-eb11-a812-000d3acba81e_TRUE"]', timeout=5000, no_wait_after=True,force=True)

            await delay()

            await page.click('input[id="315e92cb-b970-eb11-a812-000d3acba81e_TRUE"]', timeout=5000, no_wait_after=True,
                             force=True)

            # Add your code here for actions to be performed if "Yes" is selected
            # Fill in the given/first name field
            given_name = data.get("OtherGivenName", "")

            await delay()

            await page.fill('input[name="09120477-ba70-eb11-a812-000d3acba81e_GRP01022_000"]', given_name)
            # Fill in the middle names field
            middle_name = data.get("OtherMiddleName", "")
            await page.fill('input[name="ae750f7d-ba70-eb11-a812-000d3acba81e_GRP01022_000"]', middle_name)
            # Fill in the surname/family name field
            surname = data.get("OtherSurname", "")
            await page.fill('input[name="9105938a-ba70-eb11-a812-000d3acba81e_GRP01022_000"]', surname)


            # select name type
            # Get name type value from data dictionary
            name_type = data.get("NameType", "")  # Assuming "NameType" is the key for name type in the data dictionary
            if name_type:
                # Map name type value to the corresponding option value in the dropdown
                name_type_option_mapping = {
                    "Birth": "50626ce1-a95c-eb11-a812-000d3a6aba9f",
                    "Marriage": "bef6edf3-a681-eb11-a812-000d3a6a208d",
                    "English": "034310fb-a681-eb11-a812-000d3a6a208d",
                    "Preferred": "6e1e8e04-a781-eb11-a812-000d3a6a208d",
                    "Adoption": "60d7600c-a781-eb11-a812-000d3a6a208d",
                    "Other": "9df67414-a781-eb11-a812-000d3a6a208d"
                    # Add more mappings as needed
                }

                # Select the option based on the name type value from the mapping
                selected_option = name_type_option_mapping.get(name_type)

                if selected_option:
                    # Execute JavaScript to select the option in the dropdown
                    # await page.evaluate(f'''() => {{
                    #        const selectElement = document.getElementById('2ef22ecb-ba70-eb11-a812-000d3acba81e_GRP01022_000_select');
                    #        selectElement.value = "{selected_option}";
                    #    }}''')
                    await page.select_option('select[id="2ef22ecb-ba70-eb11-a812-000d3acba81e_GRP01022_000_select"]', selected_option)




        elif is_other_names.lower() == "no":
            # Perform actions if no
            await update.edit_text("You have not used other names.")
            # Click on the radio button for "No"
            await page.click('input[id="315e92cb-b970-eb11-a812-000d3acba81e_FALSE"]')
            # Add your code here for actions to be performed if "No" is selected

        else:
            print("Invalid value for 'Have you ever used any other names?' field in CSV.")

    async def Immigration_history():
        # Add your code here to handle immigration history
        country = data.get("ImmigrationCountry", "")  # Assuming "ImmigrationCountry" is the key for the country value
        await update.edit_text(f"The applicant will be in {country} when this application is submitted.")

        if country:
            # Execute JavaScript to fill the input element with the country value
            # await page.evaluate(f'''() => {{
            #         document.querySelector('input[id="79912d71-5571-eb11-a812-000d3acba96b"]').value = "{country}";
            #     }}''')

            await page.type('input[id="79912d71-5571-eb11-a812-000d3acba96b"]', country)
            await delay()
            await press_enter(page) # press enter


        # You can add more actions here if needed

        # Previous application for a New Zealand visa
        previous_application = data.get("PreviousApplication", "")

        if previous_application.lower() == "yes":
            await update.edit_text("You have previously applied for a New Zealand visa.")

            # Click on the radio button for "Yes"
            await page.click('input[id="921cbb09-c770-eb11-a812-000d3acba96b_TRUE"]')

            # Previous visa number
            previous_visa_number = data.get("PreviousVisaNumber", "")

            if previous_visa_number:
                await update.edit_text(f"The previous New Zealand visa number is {previous_visa_number}.")

                # Fill the input field for previous visa number
                await page.type('input[name="a89dd43a-c770-eb11-a812-000d3acba96b"]', previous_visa_number)

        elif previous_application.lower() == "no":
            await update.edit_text("You have not previously applied for a New Zealand visa.")

            # Click on the radio button for "No"
            await page.click('input[id="921cbb09-c770-eb11-a812-000d3acba96b_FALSE"]')

        else:
            print("Data does not exit in the csv")




        # Code to handle the radio button for "Have you previously requested an NZeTA (New Zealand Electronic Travel Authority)?"
        previous_nzeta_request = data.get("PreviousNZETARequest",
                                          "")  # Assuming "PreviousNZETARequest" is the key for the yes/no value
        if previous_nzeta_request.lower() == "yes":
            await update.edit_text("You have previously requested an NZeTA.")
            # Click on the radio button for "Yes"
            await page.click('input[id="21fa18f2-c770-eb11-a812-000d3acba96b_TRUE"]')

            # Fill the input field with the NZeTA visa number
            nzeta_visa_number = data.get("nzeta_PreviousVisaNumber", "")
            await page.fill('input[name="e40de711-c870-eb11-a812-000d3acba96b"]', nzeta_visa_number)

        elif previous_nzeta_request.lower() == "no":
            await update.edit_text("You have not previously requested an NZeTA.")
            # Click on the radio button for "No"
            await page.click('input[id="21fa18f2-c770-eb11-a812-000d3acba96b_FALSE"]')

        else:
            print("Invalid value for 'Have you previously requested an NZeTA?' field in CSV.")




        # Code to handle the radio button for "Do you hold an Australian Permanent Resident Visa?"
        australian_pr_visa = data.get("AustralianPRVisa",
                                      "")  # Assuming "AustralianPRVisa" is the key for the yes/no value
        if australian_pr_visa.lower() == "yes":
            await update.edit_text("You hold an Australian Permanent Resident Visa.")
            # Click on the radio button for "Yes"
            await page.click('input[id="73f799f6-c670-eb11-a812-000d3acba96b_TRUE"]')
        elif australian_pr_visa.lower() == "no":
            await update.edit_text("You do not hold an Australian Permanent Resident Visa.")
            # Click on the radio button for "No"
            await page.click('input[id="73f799f6-c670-eb11-a812-000d3acba96b_FALSE"]')
        else:
            print("Invalid value for 'Do you hold an Australian Permanent Resident Visa?' field in CSV.")





        # Code to handle the radio button for "Have you ever traveled to New Zealand?"
        traveled_to_nz = data.get("TraveledToNZ", "")  # Assuming "TraveledToNZ" is the key for the yes/no value
        if traveled_to_nz.lower() == "yes":
            await update.edit_text("You have traveled to New Zealand.")
            # Click on the radio button for "Yes"
            await page.click('input[id="5b0e1037-c870-eb11-a812-000d3acba96b_TRUE"]')
            # Fill the date field with month and year
            month = data.get('TraveledToNZ_Month','01')
            year = data.get('TraveledToNZ_Year', '2022')
            await page.type('input[id="2dc03555-c870-eb11-a812-000d3acba96b_date_mm"]', month)
            await page.type('input[id="2dc03555-c870-eb11-a812-000d3acba96b_date_yy"]', year)

            # Code to handle the radio button for "Will your total time in New Zealand for all visits including this proposed visit equal 24 months or more?"
            total_time_nz = data.get("TotalTimeInNZ", "")  # Assuming "TotalTimeInNZ" is the key for the yes/no value
            if total_time_nz.lower() == "yes":
                await update.edit_text("Your total time in New Zealand will equal 24 months or more.")
                # Click on the radio button for "Yes"
                await page.click('input[id="ebee4191-3788-eb11-a812-000d3acbe28e_TRUE"]')
            else:
                await update.edit_text("Your total time in New Zealand will be less than 24 months.")
                # Click on the radio button for "No"
                await page.click('input[id="ebee4191-3788-eb11-a812-000d3acbe28e_FALSE"]')





        else:
            await update.edit_text("You have not traveled to New Zealand.")
            # Click on the radio button for "No"
            await page.click('input[id="5b0e1037-c870-eb11-a812-000d3acba96b_FALSE"]')


    async def Passport_and_birth_details():

        await delay()
        # Fill Passport number input field
        passport_number = data.get("PassportNumber", "")  # Assuming "PassportNumber" is the key for the passport number

        #
        if passport_number:
            await page.type('input[id="a2a0af83-c070-eb11-a812-000d3acba96b"]', passport_number)



        # Fill Nationality input field
        nationality = data.get("Nationality", "")  # Assuming "Nationality" is the key for the nationality

        if nationality:
            await page.type('input[id="400e58a8-c070-eb11-a812-000d3acba96b"]', nationality)
            await delay(.9)
            await press_enter(page)  # press enter




        # Fill Country or territory of issue input field
        issue_country = data.get("IssueCountry", "")  # Assuming "IssueCountry" is the key for the issue country
        if issue_country:
            await page.type('input[id="a498fe9b-c070-eb11-a812-000d3acba96b"]', issue_country)
            await delay(.9)
            await press_enter(page) # press enter


        # Fill Passport issue date input fields
        issue_date = data.get("IssueDate", "")  # Assuming "IssueDate" is the key for the issue date
        if issue_date:
            # Split the date into day, month, and year
            day, month, year = issue_date.split("-")
            # Fill day input field
            await page.type('input[id="ca0f4ece-c070-eb11-a812-000d3acba96b_date_dd"]', day)
            # Fill month input field
            await page.type('input[id="ca0f4ece-c070-eb11-a812-000d3acba96b_date_mm"]', month)
            # Fill year input field
            await page.type('input[id="ca0f4ece-c070-eb11-a812-000d3acba96b_date_yy"]', year)
            await press_enter(page)

        # Fill Passport expiry date input fields
        expiry_date = data.get("ExpiryDate", "")  # Assuming "ExpiryDate" is the key for the expiry date
        if expiry_date:
            # Split the date into day, month, and year
            day, month, year = expiry_date.split("-")
            # Fill day input field
            await page.type('input[id="518553e0-c070-eb11-a812-000d3acba96b_date_dd"]', day)
            # Fill month input field
            await page.type('input[id="518553e0-c070-eb11-a812-000d3acba96b_date_mm"]', month)
            # Fill year input field
            await page.type('input[id="518553e0-c070-eb11-a812-000d3acba96b_date_yy"]', year)
            await press_enter(page)



        # Get gender value from data dictionary
        gender_value = data.get("Gender", "")  # Assuming "Gender" is the key for gender in the data dictionary
        if gender_value:
            # Map gender value to the corresponding option value in the dropdown
            gender_option_mapping = {
                "Male": "104f55f9-7260-eb11-a812-000d3a6a2b18",
                "Female": "0b030ce5-7360-eb11-a812-000d3a6a2b18",
                "Gender Diverse": "11564d40-7460-eb11-a812-000d3a6a2b18"
            }


            # Select the option based on the gender value from the mapping
            selected_option = gender_option_mapping.get(gender_value.title())
            if selected_option:
                # # Execute JavaScript to select the option in the dropdown
                # await page.evaluate(f'''() => {{
                #                document.querySelector('select[id="23c3f3d2-bd70-eb11-a812-000d3acba96b_select"]').value = "{selected_option}";
                #            }}''')

                await page.select_option('select[id="23c3f3d2-bd70-eb11-a812-000d3acba96b_select"]', selected_option)
                await press_enter(page)
            # if selected_option:
            #     # Execute JavaScript to select the option in the dropdown
            #     await page.evaluate(f'''() => {{
            #         document.querySelector('select[id="23c3f3d2-bd70-eb11-a812-000d3acba96b_select"]').value = "{selected_option}";
            #     }}''')



        # Extract date of birth from data dictionary
        dob = data.get("DateOfBirth", "")
        if dob:
            # Split date into day, month, and year
            day, month, year = dob.split('-')

            # Execute JavaScript to fill in the date of birth fields
            await page.evaluate(f'''() => {{
                document.getElementById('d8ed0619-be70-eb11-a812-000d3acba96b_date_dd').value = "{day}";
                document.getElementById('d8ed0619-be70-eb11-a812-000d3acba96b_date_mm').value = "{month}";
                
            }}''') #document.getElementById('d8ed0619-be70-eb11-a812-000d3acba96b_date_yy').value = "{year}";

            await page.type('input[id="d8ed0619-be70-eb11-a812-000d3acba96b_date_yy"]', year)
            await press_enter(page)


            # Country of Birth
            country_of_birth = data.get("CountryOfBirth", "")
            #
            # if country_of_birth:
            #     await update.edit_text(f"The country or territory of birth is {country_of_birth}.")
            #
            #     # Execute JavaScript to fill the country of birth input field
            #     await page.evaluate(f'''
            #         () => {{
            #             const inputField = document.querySelector('input[name="1614b466-be70-eb11-a812-000d3acba96b"]');
            #             inputField.value = "{country_of_birth}";
            #         }}
            #     ''')

            if country_of_birth:
                await update.edit_text(f"Filling country of birth: {country_of_birth}")

                # Execute JavaScript to focus on the input field and type the country of birth
                # await page.evaluate(f'''
                #        () => {{
                #            const inputField = document.querySelector('input[name="1614b466-be70-eb11-a812-000d3acba96b"]');
                #            inputField.focus();
                #            inputField.value = "{country_of_birth}";
                #            inputField.dispatchEvent(new Event('input', {{ bubbles: true }}));
                #        }}
                #    ''')

                await page.type('input[name="1614b466-be70-eb11-a812-000d3acba96b"]', country_of_birth)
                await delay(.9)

                # Wait for the field to appear and then press Enter
                # await page.wait_for_selector(f'div[role="option"]:has-text("{country_of_birth}")', timeout=5000)

                await press_enter(page)



                # State or province or region of birth

                state_province_region_of_birth = data.get("StateProvinceRegionOfBirth", "")

                if state_province_region_of_birth:
                    await update.edit_text(f"Filling state/province/region of birth: {state_province_region_of_birth}")

                    await page.focus('input[name="484b3bbf-bf70-eb11-a812-000d3acba96b"]')
                    await page.keyboard.type(state_province_region_of_birth)
                    await press_enter(page)
                else:
                    print("State/Province/Region of birth is empty in the data.")



                await press_enter(page)  # press enter
                await delay(.9)



            # Town or City of Birth
            city_of_birth = data.get("CityOfBirth", "")

            if city_of_birth:
                await update.edit_text(f"The town or city of birth is {city_of_birth}.")

                # Execute JavaScript to fill the town or city of birth input field
                await page.evaluate(f'''
                    () => {{
                        const inputField = document.querySelector('input[name="36bbd2cb-bf70-eb11-a812-000d3acba96b"]');
                        inputField.value = "{city_of_birth}";
                    }}
                ''')


    async def handle_other_citizenship():
        other_citizenship = data.get("OtherCitizenship",
                                     "")  # Assuming "OtherCitizenship" is the key for the yes/no value

        if other_citizenship.lower() == "yes":
            await update.edit_text("You hold other citizenships.")

            # Click on the radio button for "Yes"
            await page.click('input[id="ec7a3d57-c170-eb11-a812-000d3acba96b_TRUE"]')

            # Add your code here for actions to be performed if "Yes" is selected
            # This can include filling in additional fields or performing other actions

        elif other_citizenship.lower() == "no":
            await update.edit_text("You do not hold any other citizenships.")

            # Click on the radio button for "No"
            await page.click('input[id="ec7a3d57-c170-eb11-a812-000d3acba96b_FALSE"]')

            # Add your code here for actions to be performed if "No" is selected
            # This can include skipping certain fields or performing other actions

        else:
            print("Invalid value for 'Do you hold any other citizenships?' field in CSV.")

    # async def handle_new_contact_details_country():
    #
    #     # Country
    #     current_country = data.get("CurrentCountry",
    #                                "")  # Assuming "CurrentCountry" is the key for the current country value
    #
    #     if current_country:
    #         await update.edit_text(f"The current country or territory is {current_country}.")
    #
    #         # Fill the current country or territory input field
    #         await page.type('input[name="83a5117e-c570-eb11-a812-000d3acba96b_GRP01045_000"]', current_country)
    #
    #
    # # Postal Code
    #
    # postal_same_as_physical = data.get("PostalSameAsPhysical",
    #                                    "")  # Assuming "PostalSameAsPhysical" is the key for the yes/no value
    #
    # if postal_same_as_physical.lower() == "yes":
    #     await update.edit_text("The postal address is the same as the physical address.")
    #
    #     # Click on the radio button for "Yes"
    #     await page.click('input[id="34fd122e-5471-eb11-a812-000d3acba96b_TRUE"]')
    #
    # elif postal_same_as_physical.lower() == "no":
    #     await update.edit_text("The postal address is different from the physical address.")
    #
    #     # Click on the radio button for "No"
    #     await page.click('input[id="34fd122e-5471-eb11-a812-000d3acba96b_FALSE"]')
    #
    # else:
    #     print("Invalid value for 'Is your postal address the same as your physical address?' field in CSV.")
    #
    # email_address = data.get("EmailAddress", "")
    # phone_number = data.get("PhoneNumber", "")
    # alt_phone_number = data.get("AlternativePhoneNumber", "")
    #
    # if email_address:
    #     await update.edit_text(f"The email address is {email_address}.")
    #     await page.type('input[name="777c9ef8-5671-eb11-a812-000d3acba96b_GRP01043_000"]', email_address)
    #
    # if phone_number:
    #     await update.edit_text(f"The applicant's preferred contact number is {phone_number}.")
    #     await page.type('input[name="2a26325e-5671-eb11-a812-000d3acba96b_GRP01102_000"]', phone_number)
    #
    # if alt_phone_number:
    #     await update.edit_text(f"The alternative phone number is {alt_phone_number}.")
    #     await page.type('input[name="b8a80463-bc11-ec11-b6e6-002248100335_GRP01103_000"]', alt_phone_number)

    async def handle_new_contact_details_country():
        # Country
        current_country = data.get("CurrentCountry", "")

        if current_country:
            await update.edit_text(f"The current country or territory is {current_country}.")

            # Execute JavaScript to fill the current country or territory input field
            # await page.evaluate(f'''
            #     () => {{
            #         const inputField = document.querySelector('input[name="83a5117e-c570-eb11-a812-000d3acba96b_GRP01045_000"]');
            #         inputField.value = "{current_country}";
            #     }}
            # ''')

            await page.type('input[name="83a5117e-c570-eb11-a812-000d3acba96b_GRP01045_000"]', current_country)
            await press_enter(page) # press enter
            await delay(.9)

            # Addrss
            address = data.get("ContactAddress", "")
            await update.edit_text(f"Filling address: {address}")
            await page.type('input[name="7333304e-c570-eb11-a812-000d3acba96b_GRP01045_000_address"]', address)
            await press_enter(page)  # press enter



        # Postal Code
        postal_same_as_physical = data.get("PostalSameAsPhysical", "").lower()

        if postal_same_as_physical == "yes":
            await update.edit_text("The postal address is the same as the physical address.")

            # Execute JavaScript to click on the radio button for "Yes"
            await page.evaluate('''
                () => {
                    document.getElementById("34fd122e-5471-eb11-a812-000d3acba96b_TRUE").click();
                }
            ''')

        elif postal_same_as_physical == "no":
            await update.edit_text("The postal address is different from the physical address.")

            # Execute JavaScript to click on the radio button for "No"
            await page.evaluate('''
                () => {
                    document.getElementById("34fd122e-5471-eb11-a812-000d3acba96b_FALSE").click();
                }
            ''')

        else:
            print("Invalid value for 'Is your postal address the same as your physical address?' field in CSV.")

        email_address = data.get("EmailAddress", "")
        phone_number = data.get("PhoneNumber", "")
        alt_phone_number = data.get("AlternativePhoneNumber", "")

        if email_address:
            await update.edit_text(f"The email address is {email_address}.")

            # Execute JavaScript to fill the email address input field
            await page.evaluate(f'''
                () => {{
                    const inputField = document.querySelector('input[name="777c9ef8-5671-eb11-a812-000d3acba96b_GRP01043_000"]');
                    inputField.value = "{email_address}";
                }}
            ''')

        if phone_number:
            await update.edit_text(f"The applicant's preferred contact number is {phone_number}.")

            # Execute JavaScript to fill the phone number input field
            await page.evaluate(f'''
                () => {{
                    const inputField = document.querySelector('input[name="2a26325e-5671-eb11-a812-000d3acba96b_GRP01102_000"]');
                    inputField.value = "{phone_number}";
                }}
            ''')

        if alt_phone_number:
            await update.edit_text(f"The alternative phone number is {alt_phone_number}.")

            # Execute JavaScript to fill the alternative phone number input field
            await page.evaluate(f'''
                () => {{
                    const inputField = document.querySelector('input[name="b8a80463-bc11-ec11-b6e6-002248100335_GRP01103_000"]');
                    inputField.value = "{alt_phone_number}";
                }}
            ''')

    async def handlePoliceCertificates():
        option = data.get('handlePoliceCertificates','yes')
        print('option', option)
        if option.lower() == "yes":

            # Execute JavaScript to click the "Yes" radio button  was_certificate_issued_within_last_24_months


            await page.evaluate('''() => {
                    document.getElementById('d00a375a-4288-eb11-a812-000d3acbe28e_GRP01153_000_TRUE').click();
                }''')

            was_certificate_issued_within_last_24_months = data.get("was_certificate_issued_within_last_24_months")


            await page.evaluate('''() => {
                            document.getElementById('b12ff4ba-4588-eb11-a812-000d3acbe28e_GRP01153_000_TRUE').click();
                        }''')


        elif option.lower() == "no":
            await page.evaluate('''() => {
                               document.getElementById('d00a375a-4288-eb11-a812-000d3acbe28e_GRP01153_000_FALSE').click();
                           }''')
            # Handle the case when the option is "no"
            issue_date = data.get("issue_date", "01-01-2022")  # Example date format: "01-01-2022"
            day, month, year = issue_date.split('-')

            await page.type('input[name="1e76aa90-4888-eb11-a812-000d3acbe28e_GRP01153_000_date_dd"]', day)
            await page.type('input[name="1e76aa90-4888-eb11-a812-000d3acbe28e_GRP01153_000_date_mm"]', month)
            await page.type('input[name="1e76aa90-4888-eb11-a812-000d3acbe28e_GRP01153_000_date_yy"]', year)

            country_of_issue = data.get("country_of_issue", "Country")  # Example country
            await page.type('input[name="3d14c930-d8dd-eb11-bacb-0022480ff4f5_GRP01153_000"]', country_of_issue)

            await press_enter(page)

            await page.select_option('select[name="b85f52d4-4888-eb11-a812-000d3acbe28e_GRP01153_000"]',
                                     value="1")  # Assuming "Yes" for English


    async def handle_national_identity():
        # Retrieve the data using data.get()
        has_national_id = data.get('has_national_id', '').lower().strip()
        print('has_national_id',has_national_id)

        if has_national_id == "yes":
            # Click the "Yes" radio button

            # await page.click('#ffebbef8-c070-eb11-a812-000d3acba96b_TRUE_label')



            script = '''
               () => {
                   const yesRadio = document.getElementById('ffebbef8-c070-eb11-a812-000d3acba96b_TRUE');
                   yesRadio.click();
               }'''

            await page.evaluate(script)
            #
            # await page.evaluate('''() => {
            #                 document.getElementById('ffebbef8-c070-eb11-a812-000d3acba96b_TRUE').click();
            #             }''')

            # print("clickignnnnnnnnn")
            #
            # await page.click('input[name="ffebbef8-c070-eb11-a812-000d3acba96b_TRUE"]')



            # Retrieve the national identity number using data.get()
            national_id_number = data.get('national_id_number', '')
            # Input the national identity number 'input[name="9da8b14a-c170-eb11-a812-000d3acba96b"]'
            await page.type('input[name="5f03e825-c170-eb11-a812-000d3acba96b"]', national_id_number)
            await delay()
            await press_enter(page)

            country_of_issue = data.get('country_of_issue', '')
            # Input the country or territory of issue into the input field
            await page.type('input[name="9da8b14a-c170-eb11-a812-000d3acba96b"]', country_of_issue)
            await delay()
            await press_enter(page)


        elif has_national_id == "no":
            # Click the "No" radio button
            script = '''
            () => {
                const noRadio = document.getElementById('ffebbef8-c070-eb11-a812-000d3acba96b_FALSE');
                noRadio.click();
            }'''

            await page.evaluate(script)

    try:
        # Call the nested function
        await click_radio_button()
        await handle_other_names()
        await Immigration_history()

        await Passport_and_birth_details()
        await delay()
        await handlePoliceCertificates()
    except Exception as e:
        print(e)

    await handle_national_identity()
    await delay()
    await handle_other_citizenship()
    await handle_new_contact_details_country()



# async def fourth_page(page, data):
#     # Get the required data
#     membership = data.get("membership_with_immigration_nz_tourism_partners")
#     financial_support = data.get("financial_support_during_stay")
#     prepaid_accommodation = data.get("prepaid_accommodation")
#     available_funds = data.get("available_funds")
#
#     # Check if the membership data is available
#     if membership is not None:
#         # Find the radio button based on the membership value
#         if membership.lower() == "yes":
#             # Click the Yes radio button
#             await page.click('#3d8b63a8-4880-eb11-a812-000d3a6a208d_TRUE')
#         elif membership.lower() == "no":
#             # Click the No radio button
#             await page.click('#3d8b63a8-4880-eb11-a812-000d3a6a208d_FALSE')
#         else:
#             print("Invalid input for membership. Please provide 'yes' or 'no'.")
#     else:
#         print("Membership data not found.")
#
#
#
#     async def finance_support():
#
#         # Handle financial support question
#         if financial_support.lower() == "yes":
#             # Click the Yes radio button
#             await page.click('#22297816-d481-eb11-a812-000d3a6a208d_TRUE')
#             # Handle prepaid accommodation question
#             if prepaid_accommodation.lower() == "yes":
#                 # Click the Yes radio button
#                 await page.click('#dd02e051-d481-eb11-a812-000d3a6a208d_TRUE')
#                 # Type the address if available
#                 accommodation_address = data.get("accommodation_address")
#                 if accommodation_address:
#                     await page.type('#05d63bc3-dfc7-eb11-bacc-0022480fefa6_GRP01095_000_address', accommodation_address)
#             elif prepaid_accommodation.lower() == "no":
#                 # Click the No radio button
#                 await page.click('#dd02e051-d481-eb11-a812-000d3a6a208d_FALSE')
#             else:
#                 print("Invalid input for prepaid accommodation. Please provide 'yes' or 'no'.")
#
#             # Handle
#             # available
#             # funds
#             # question
#             if available_funds.lower() == "yes":
#                 # Click the Yes radio button
#                 await page.click('#dd02e051-d481-eb11-a812-000d3a6a208d_TRUE')
#             elif available_funds.lower() == "no":
#                 # Click the No radio button
#                 await page.click('#dd02e051-d481-eb11-a812-000d3a6a208d_FALSE')
#                 # Fill the textarea for explanation
#                 explanation = data.get("available_funds_explanation")
#                 if explanation:
#                     await page.type('#d17de421-d681-eb11-a812-000d3a6a208d', explanation)
#                 else:
#                     print("Explanation for available funds not provided.")
#             else:
#                 print("Invalid input for available funds. Please provide 'yes' or 'no'.")
#
#
#         elif financial_support.lower() == "no":
#             # Click the No radio button
#             await page.click('#22297816-d481-eb11-a812-000d3a6a208d_FALSE')
#         else:
#             print("Invalid input for financial support. Please provide 'yes' or 'no'.")
#
#



async def fourth_page(page, data):
    # Navigate to the page and wait for it to fully load
    # Navigate to the page and wait for it to fully load
    await page.wait_for_load_state(state='networkidle', timeout=120000)
    # Get the required data
    membership = data.get("membership_with_immigration_nz_tourism_partners")
    financial_support = data.get("financial_support_during_stay")
    prepaid_accommodation = data.get("prepaid_accommodation")
    available_funds = data.get("available_funds")
    onward_travel_evidence = data.get("onward_travel_evidence")

    # Check if the membership data is available
    if membership is not None:
        # Find the radio button based on the membership value
        if membership.lower() == "yes":
            # Click the Yes radio button
            await page.evaluate('''() => {
                document.getElementById('3d8b63a8-4880-eb11-a812-000d3a6a208d_TRUE').click();
            }''')
        elif membership.lower() == "no":
            # Click the No radio button
            await page.evaluate('''() => {
                document.getElementById('3d8b63a8-4880-eb11-a812-000d3a6a208d_FALSE').click();
            }''')
        else:
            print("Invalid input for membership. Please provide 'yes' or 'no'.")
    else:
        print("Membership data not found.")

    # Handle financial support question
    async def finance_support():
        # Handle financial support question
        if financial_support.lower() == "yes":
            # Click the Yes radio button
            await page.evaluate('''() => {
                document.getElementById('31a89c11-4e81-eb11-a812-000d3a6a208d_TRUE').click();
            }''')

            await delay()
            # Handle prepaid accommodation question
            if prepaid_accommodation.lower() == "yes":
                # Click the Yes radio button
                await page.evaluate('''() => {
                    document.getElementById('22297816-d481-eb11-a812-000d3a6a208d_TRUE').click();
                }''')

                await delay()
                # Type the address if available
                accommodation_address = data.get("accommodation_address")
                if accommodation_address:
                    await page.evaluate('''(address) => {
                        document.getElementById('05d63bc3-dfc7-eb11-bacc-0022480fefa6_GRP01095_000_address').value = address;
                    }''', accommodation_address)

                    await delay()

            elif prepaid_accommodation.lower() == "no":
                # Click the No radio button
                await page.evaluate('''() => {
                    document.getElementById('22297816-d481-eb11-a812-000d3a6a208d_FALSE').click();
                }''')
                await delay()
            else:
                print("Invalid input for prepaid accommodation. Please provide 'yes' or 'no'.")

            # Handle available funds question
            if available_funds.lower() == "yes":
                # Click the Yes radio button
                await page.evaluate('''() => {
                    document.getElementById('dd02e051-d481-eb11-a812-000d3a6a208d_TRUE').click();
                }''')

                await delay()
            elif available_funds.lower() == "no":
                # Click the No radio button
                await page.evaluate('''() => {
                    document.getElementById('dd02e051-d481-eb11-a812-000d3a6a208d_FALSE').click();
                }''')

                await delay()
                # Fill the textarea for explanation
                explanation = data.get("available_funds_explanation")
                if explanation:
                    await page.evaluate('''(explanation) => {
                        document.getElementById('d17de421-d681-eb11-a812-000d3a6a208d').value = explanation;
                    }''', explanation)

                    await delay()
                else:
                    print("Explanation for available funds not provided.")
            else:
                print("Invalid input for available funds. Please provide 'yes' or 'no'.")

            # Select onward travel evidence from dropdown



            if onward_travel_evidence:
                # Execute JavaScript to select the option from the dropdown based on text value
                await page.evaluate('''(text) => {
                        const selectElement = document.getElementById('93c0dc76-db81-eb11-a812-000d3a6a208d_select');
                        const options = selectElement.options;
                        for (let option of options) {
                            if (option.text === text) {
                                option.selected = true;
                                break;
                            }
                        }
                        selectElement.dispatchEvent(new Event('change'));
                    }''', onward_travel_evidence.strip())
            else:
                print("Onward travel evidence not provided.")



        elif financial_support.lower() == "no":
            # Click the No radio button
            await page.evaluate('''() => {
                document.getElementById('31a89c11-4e81-eb11-a812-000d3a6a208d_FALSE').click();
            }''')

            await delay()

            # Execute JavaScript to click the "Yes" radio button
            await page.evaluate('''document.getElementById("615e626b-4e81-eb11-a812-000d3a6a208d_TRUE").click()''')


        else:
            print("Invalid input for financial support. Please provide 'yes' or 'no'.")



    async def multiple_journey_visa():
        answer = data.get("Do_you_require_a_multiple_journey_visa",'yes')

        if answer.lower() == "yes":
            await page.evaluate('''document.getElementById("4ecce740-c712-ed11-b83d-00224891e8df_TRUE").click()''')

            # Fill in the estimated date of arrival in New Zealand
            arrival_date = data.get("MJV_arrival_date", "01-06-2025")
            day, month, year = arrival_date.split('-')
            await page.type('input[name="c8ed1866-dd81-eb11-a812-000d3a6a208d_date_dd"]', day)
            await page.type('input[name="c8ed1866-dd81-eb11-a812-000d3a6a208d_date_mm"]', month)
            await page.type('input[name="c8ed1866-dd81-eb11-a812-000d3a6a208d_date_yy"]', year)

            # Fill in the estimated date of departure from New Zealand
            departure_date = data.get("MJV_departure_date", "01-06-2025")
            day, month, year = departure_date.split('-')
            await page.type('input[name="b47ea2bb-aec4-eb11-bacc-000d3ad17b60_date_dd"]', day)
            await page.type('input[name="b47ea2bb-aec4-eb11-bacc-000d3ad17b60_date_mm"]', month)
            await page.type('input[name="b47ea2bb-aec4-eb11-bacc-000d3ad17b60_date_yy"]', year)

        elif answer.lower() == "no":
            await page.evaluate('''document.getElementById("4ecce740-c712-ed11-b83d-00224891e8df_FALSE").click()''')

            # Fill in the estimated date of arrival in New Zealand
            arrival_date = data.get("MJV_arrival_date", "01-06-2025")
            day, month, year = arrival_date.split('-')
            await page.type('input[name="c8ed1866-dd81-eb11-a812-000d3a6a208d_date_dd"]', day)
            await page.type('input[name="c8ed1866-dd81-eb11-a812-000d3a6a208d_date_mm"]', month)
            await page.type('input[name="c8ed1866-dd81-eb11-a812-000d3a6a208d_date_yy"]', year)

            # Fill in the estimated date of departure from New Zealand
            departure_date = data.get("MJV_departure_date", "01-06-2025")
            day, month, year = departure_date.split('-')
            await page.type('input[name="7b071dfd-dd81-eb11-a812-000d3a6a208d_date_dd"]', day)
            await page.type('input[name="7b071dfd-dd81-eb11-a812-000d3a6a208d_date_mm"]', month)
            await page.type('input[name="7b071dfd-dd81-eb11-a812-000d3a6a208d_date_yy"]', year)

        else:
            print("Invalid answer. Please provide 'yes' or 'no'.")




        # Extract the value from data.get
        selected_option_text = data.get("Parental_permission")

        # Check if the text exists and is a valid option in the dropdown
        if selected_option_text:
            # Execute JavaScript to select the option from the dropdown based on its text
            await page.evaluate('''(text) => {
                const selectElement = document.getElementById('bffffd50-df81-eb11-a812-000d3a6a208d_select');
                const options = selectElement.options;
                for (let option of options) {
                    if (option.text === text) {
                        option.selected = true;
                        break;
                    }
                }
                selectElement.dispatchEvent(new Event('change'));
            }''', selected_option_text)



    try:
        await finance_support()
        await multiple_journey_visa()
    except Exception as e:
        print(e)



# async def fifth_page(page, data):
#
#     async def handle_boolean_radio():
#         conviction_value = data.get("Conviction")
#         if conviction_value:
#             value = conviction_value.lower().strip()  # Convert to lowercase and remove leading/trailing spaces
#             if value == "yes":
#                 await page.evaluate('document.getElementById("57903c97-ee60-eb11-a812-000d3a6a20d4_TRUE").click();')
#                 # Fill in the first text input field
#                 await page.evaluate('document.getElementById("a64b185b-cf61-eb11-a812-000d3a6a2b18_GRP01002_000").value = arguments[0];', data.get("Offence", ""))
#                 # Fill in the textarea
#                 await page.evaluate('document.getElementById("717feb7e-d061-eb11-a812-000d3a6a2b18_GRP01002_000").value = arguments[0];', data.get("ConvictionDetails", ""))
#             elif value == "no":
#                 await page.evaluate('document.getElementById("57903c97-ee60-eb11-a812-000d3a6a20d4_FALSE").click();')
#
#     async def handle_investigation_radio():
#         investigation_value = data.get("UnderInvestigation")
#         if investigation_value:
#             value = investigation_value.lower().strip()  # Convert to lowercase and remove leading/trailing spaces
#             if value == "yes":
#                 await page.evaluate('document.getElementById("8226d007-49d6-ec11-a7b5-000d3acc5483_TRUE").click();')
#                 # Fill in the textarea
#                 await page.evaluate(
#                     'document.getElementById("7531b12a-d161-eb11-a812-000d3a6a2b18").value = arguments[0];',
#                     data.get("InvestigationDetails", ""))
#             elif value == "no":
#                 await page.evaluate('document.getElementById("8226d007-49d6-ec11-a7b5-000d3acc5483_FALSE").click();')
#
#     async def handle_expulsion_radio():
#         expulsion_value = data.get("Expulsion")
#         if expulsion_value:
#             value = expulsion_value.lower().strip()  # Convert to lowercase and remove leading/trailing spaces
#             if value == "yes":
#                 await page.evaluate('document.getElementById("24eff85a-d161-eb11-a812-000d3a6a2b18_TRUE").click();')
#                 # Fill in the textarea
#                 await page.evaluate(
#                     'document.getElementById("1039edf5-d461-eb11-a812-000d3a6a2b18").value = arguments[0];',
#                     data.get("ExpulsionDetails", ""))
#             elif value == "no":
#                 await page.evaluate('document.getElementById("24eff85a-d161-eb11-a812-000d3a6a2b18_FALSE").click();')
#
#     async def handle_refusal_radio():
#         refusal_value = data.get("Refusal")
#         if refusal_value:
#             value = refusal_value.lower().strip()  # Convert to lowercase and remove leading/trailing spaces
#             if value == "yes":
#                 await page.evaluate('document.getElementById("81b59915-d661-eb11-a812-000d3a6a2b18_TRUE").click();')
#                 # Fill in the country or territory input field
#                 await page.evaluate(
#                     'document.getElementById("79f6fe50-d761-eb11-a812-000d3a6a2b18_GRP01003_000").value = arguments[0];',
#                     data.get("RefusalCountry", ""))
#                 # Fill in the visa or permit type input field
#                 await page.evaluate(
#                     'document.getElementById("b6a5f877-d761-eb11-a812-000d3a6a2b18_GRP01003_000").value = arguments[0];',
#                     data.get("VisaPermitType", ""))
#                 # Fill in the date of refusal input field
#                 await page.type('input[name="3837f0aa-d761-eb11-a812-000d3a6a2b18_GRP01003_000_date_mm"]',
#                                 data.get("MonthOfRefusal", ""))
#                 await page.type('input[name="3837f0aa-d761-eb11-a812-000d3a6a2b18_GRP01003_000_date_yy"]',
#                                 data.get("YearOfRefusal", ""))
#
#                 await page.type('textarea[name="6a21927e-da61-eb11-a812-000d3a6a2b18"]', data.get("Maximum_of_500_characters"))
#
#
#             elif value == "no":
#                 await page.evaluate('document.getElementById("81b59915-d661-eb11-a812-000d3a6a2b18_FALSE").click();')
#
#     async def handle_lived_in_country_radio():
#         lived_in_country_value = data.get("LivedInCountry")
#         if lived_in_country_value:
#             value = lived_in_country_value.lower().strip()  # Convert to lowercase and remove leading/trailing spaces
#             if value == "yes":
#                 # Click on the radio button for "yes"
#                 await page.evaluate('document.querySelector(".boolean-radio input[value=\'Yes\']").click();')
#                 # Fill in the country input field
#                 await page.type('input[name="108cce82-dd61-eb11-a812-000d3a6a2b18_GRP01001_000"]', data.get('CountryNameHere'))
#             elif value == "no":
#                 # Click on the radio button for "no"
#                 await page.evaluate('document.querySelector(".boolean-radio input[value=\'No\']").click();')
#
#

async def fifth_page(page, data):
    # Navigate to the page and wait for it to fully load
    await page.wait_for_load_state(state='networkidle', timeout=120000)

    async def handle_boolean_radio():
        conviction_value = data.get("Conviction")
        if conviction_value:
            value = conviction_value.lower().strip()  # Convert to lowercase and remove leading/trailing spaces
            if value == "yes":
                await page.evaluate('document.getElementById("57903c97-ee60-eb11-a812-000d3a6a20d4_TRUE").click();')
                await delay(0.5)
                await page.evaluate('''(offence) => {
                    document.getElementById("a64b185b-cf61-eb11-a812-000d3a6a2b18_GRP01002_000").value = offence;
                }''', data.get("Offence", ""))
                await delay(0.5)
                await page.evaluate('''(convictionDetails) => {
                    document.getElementById("717feb7e-d061-eb11-a812-000d3a6a2b18_GRP01002_000").value = convictionDetails;
                }''', data.get("ConvictionDetails", ""))
            elif value == "no":
                await page.evaluate('document.getElementById("57903c97-ee60-eb11-a812-000d3a6a20d4_FALSE").click();')

    async def handle_investigation_radio():
        investigation_value = data.get("UnderInvestigation")
        if investigation_value:
            value = investigation_value.lower().strip()  # Convert to lowercase and remove leading/trailing spaces
            if value == "yes":
                await page.evaluate('document.getElementById("8226d007-49d6-ec11-a7b5-000d3acc5483_TRUE").click();')
                await delay(0.5)
                await page.evaluate('''(investigationDetails) => {
                    document.getElementById("7531b12a-d161-eb11-a812-000d3a6a2b18").value = investigationDetails;
                }''', data.get("InvestigationDetails", ""))
            elif value == "no":
                await page.evaluate('document.getElementById("8226d007-49d6-ec11-a7b5-000d3acc5483_FALSE").click();')

    async def handle_expulsion_radio():
        expulsion_value = data.get("Expulsion")
        if expulsion_value:
            value = expulsion_value.lower().strip()  # Convert to lowercase and remove leading/trailing spaces
            if value == "yes":
                await page.evaluate('document.getElementById("24eff85a-d161-eb11-a812-000d3a6a2b18_TRUE").click();')
                await delay(0.5)
                expulsion_details = data.get("ExpulsionDetails", "")
                print("expulsion_details",expulsion_details)
                await page.type('textarea[name="1039edf5-d461-eb11-a812-000d3a6a2b18"]', expulsion_details)

            elif value == "no":
                await page.evaluate('document.getElementById("24eff85a-d161-eb11-a812-000d3a6a2b18_FALSE").click();')

    # async def handle_refusal_radio():
    #     refusal_value = data.get("Refusal")
    #     if refusal_value:
    #         value = refusal_value.lower().strip()  # Convert to lowercase and remove leading/trailing spaces
    #         if value == "yes":
    #             await page.evaluate('document.getElementById("81b59915-d661-eb11-a812-000d3a6a2b18_TRUE").click();')
    #             await delay(0.5)
    #             await page.evaluate('''(refusalCountry, visaPermitType, monthOfRefusal, yearOfRefusal, refusalDetails) => {
    #                 document.getElementById("79f6fe50-d761-eb11-a812-000d3a6a2b18_GRP01003_000").value = refusalCountry;
    #             }''', data.get("RefusalCountry", ""))
    #
    #             await press_enter(page)
    #             await delay(0.5)
    #             await page.evaluate('''(refusalCountry, visaPermitType, monthOfRefusal, yearOfRefusal, refusalDetails) => {
    #                 document.getElementById("b6a5f877-d761-eb11-a812-000d3a6a2b18_GRP01003_000").value = visaPermitType;
    #             }''', data.get("VisaPermitType", ""))
    #             await delay(0.5)
    #             await page.type('input[name="3837f0aa-d761-eb11-a812-000d3a6a2b18_GRP01003_000_date_mm"]', data.get("MonthOfRefusal", ""))
    #             await page.type('input[name="3837f0aa-d761-eb11-a812-000d3a6a2b18_GRP01003_000_date_yy"]', data.get("YearOfRefusal", ""))
    #             await delay(0.5)
    #             await page.type('textarea[name="6a21927e-da61-eb11-a812-000d3a6a2b18"]', data.get("Maximum_of_500_characters", ""))
    #         elif value == "no":
    #             await page.evaluate('document.getElementById("81b59915-d661-eb11-a812-000d3a6a2b18_FALSE").click();')

    async def handle_refusal_radio():
        refusal_value = data.get("Refusal")
        if refusal_value:
            value = refusal_value.lower().strip()  # Convert to lowercase and remove leading/trailing spaces
            if value == "yes":
                # Click on the radio button for "yes"
                await page.evaluate('''() => {
                    document.getElementById("81b59915-d661-eb11-a812-000d3a6a2b18_TRUE").click();
                }''')
                # Set the refusal country value
                refusal_country = data.get("RefusalCountry", "")
                await page.type('input[name="79f6fe50-d761-eb11-a812-000d3a6a2b18_GRP01003_000"]', refusal_country)
                await press_enter(page)
                await delay(0.5)
                # Set the visa or permit type value
                visa_permit_type = data.get("VisaPermitType", "")
                await page.type('input[name="b6a5f877-d761-eb11-a812-000d3a6a2b18_GRP01003_000"]', visa_permit_type)
                await delay(0.5)
                # Set the date of refusal values
                await page.type('input[name="3837f0aa-d761-eb11-a812-000d3a6a2b18_GRP01003_000_date_mm"]',
                                data.get("MonthOfRefusal", ""))
                await page.type('input[name="3837f0aa-d761-eb11-a812-000d3a6a2b18_GRP01003_000_date_yy"]',
                                data.get("YearOfRefusal", ""))
                await delay(0.5)
                # Set the refusal details value
                await page.type('textarea[name="6a21927e-da61-eb11-a812-000d3a6a2b18"]',
                                data.get("Maximum_of_500_characters", ""))
            elif value == "no":
                # Click on the radio button for "no"
                await page.evaluate('document.getElementById("81b59915-d661-eb11-a812-000d3a6a2b18_FALSE").click();')

    async def handle_lived_in_country_radio():
        lived_in_country_value = data.get("LivedInCountry")
        if lived_in_country_value:
            value = lived_in_country_value.lower().strip()  # Convert to lowercase and remove leading/trailing spaces
            if value == "yes":
                await page.evaluate('''(countryName) => {
                      document.getElementById("325e35b3-da61-eb11-a812-000d3a6a2b18_TRUE").click();
                  }''')
                await delay(0.5)
                await page.type('input[name="108cce82-dd61-eb11-a812-000d3a6a2b18_GRP01001_000"]',
                                data.get('CountryNameHere', ""))

                await press_enter(page)

            elif value == "no":
                await page.evaluate('document.getElementById("325e35b3-da61-eb11-a812-000d3a6a2b18_FALSE").click();')

    async def handle_police_certificate_question():
        certificate_value = data.get("PoliceCertificateProvided")
        if certificate_value:
            value = certificate_value.lower().strip()  # Convert to lowercase and remove leading/trailing spaces
            if value == "yes":
                await page.evaluate('''() => {
                    document.getElementById("873dd8ee-b08d-eb11-b1ac-000d3a6b2176_GRP01001_000_TRUE").click();
                }''')
                await delay(0.5)

                # Now, handle another question if the answer is "Yes" for providing a police certificate
                last_24_months_value = data.get("PoliceCertificateLast24Months")
                if last_24_months_value:
                    last_24_months = last_24_months_value.lower().strip()
                    if last_24_months == "yes":
                        await page.evaluate('''() => {
                            document.getElementById("c3075969-b28d-eb11-b1ac-000d3a6b2176_GRP01001_000_TRUE").click();
                        }''')
                    elif last_24_months == "no":
                        await page.evaluate('''() => {
                            document.getElementById("c3075969-b28d-eb11-b1ac-000d3a6b2176_GRP01001_000_FALSE").click();
                        }''')
            elif value == "no":
                await page.evaluate('''() => {
                    document.getElementById("873dd8ee-b08d-eb11-b1ac-000d3a6b2176_GRP01001_000_FALSE").click();
                }''')

    # Call the function
    try:
        await handle_boolean_radio()
        await handle_investigation_radio()
        # Call the function
        await handle_expulsion_radio()
        # Call the function
        await handle_refusal_radio()
        # Call the function
        await handle_lived_in_country_radio()
        await handle_police_certificate_question()
    except Exception as e:
        print(e)




async def sixth_page(page, data):
    # Navigate to the page and wait for it to fully load
    # Navigate to the page and wait for it to fully load
    await page.wait_for_load_state(state='networkidle', timeout=120000)
    async def handle_tuberculosis_radio():
        tuberculosis_value = data.get("Tuberculosis")
        if tuberculosis_value:
            value = tuberculosis_value.lower().strip()
            if value == "yes":
                await page.evaluate('document.getElementById("043d06cc-f060-eb11-a812-000d3a6a20d4_TRUE").click();')

                # Now handle the textarea
                await page.type('textarea[name="85dc1447-f160-eb11-a812-000d3a6a20d4"]', data.get("TuberculosisDetails", ""))

            elif value == "no":
                await page.evaluate('document.getElementById("043d06cc-f060-eb11-a812-000d3a6a20d4_FALSE").click();')

    async def handle_renal_dialysis_radio():
        renal_dialysis_value = data.get("RenalDialysis")
        if renal_dialysis_value:
            value = renal_dialysis_value.lower().strip()
            if value == "yes":
                await page.evaluate('document.getElementById("5d25f538-129f-eb11-b1ac-000d3a6b2264_TRUE").click();')

                # Now handle the textarea
                await page.type('textarea[name="75607abf-0261-eb11-a812-000d3a6a20d4"]', data.get("RenalDialysisDetails", ""))

            elif value == "no":
                await page.evaluate('document.getElementById("5d25f538-129f-eb11-b1ac-000d3a6b2264_FALSE").click();')

    async def handle_hospital_care_radio():
        hospital_care_value = data.get("HospitalCare")
        if hospital_care_value:
            value = hospital_care_value.lower().strip()
            if value == "yes":
                await page.evaluate('document.getElementById("5575b82a-0361-eb11-a812-000d3a6a20d4_TRUE").click();')

                # Now handle the textarea
                await page.type('textarea[name="41497256-0361-eb11-a812-000d3a6a20d4"]', data.get("HospitalCareDetails", ""))

            elif value == "no":
                await page.evaluate('document.getElementById("5575b82a-0361-eb11-a812-000d3a6a20d4_FALSE").click();')

    async def handle_residential_care_radio():
        residential_care_value = data.get("ResidentialCare")
        if residential_care_value:
            value = residential_care_value.lower().strip()
            if value == "yes":
                await page.evaluate('document.getElementById("bf3155d2-0361-eb11-a812-000d3a6a20d4_TRUE").click();')

                # Now handle the textarea
                await page.type('textarea[name="ead9a911-0461-eb11-a812-000d3a6a20d4"]', data.get("ResidentialCareDetails", ""))

            elif value == "no":
                await page.evaluate('document.getElementById("bf3155d2-0361-eb11-a812-000d3a6a20d4_FALSE").click();')

    async def handle_stay_duration_dropdown():
        stay_duration_text = data.get("StayDuration")
        if stay_duration_text:
            await page.select_option('select[name="e9fea184-0385-eb11-a812-000d3acbea15_select"]', label=stay_duration_text)


    async def handle_previous_medical_examination_radio():
        previous_exam_value = data.get("PreviousMedicalExamination")
        if previous_exam_value:
            value = previous_exam_value.lower().strip()
            if value == "yes":
                await page.evaluate('document.getElementById("d9658c1c-b1e6-ec11-bb3c-002248112af0_TRUE").click();')

                # Now handle the input field
                await page.type('input[name="9d2a875b-74fa-ed11-8f6e-00224893311a"]',
                                data.get("PreviousExamDetails", ""))

            elif value == "no":
                await page.evaluate('document.getElementById("d9658c1c-b1e6-ec11-bb3c-002248112af0_FALSE").click();')

    async def handle_current_medical_examination_radio():
        current_exam_value = data.get("CurrentMedicalExamination")
        if current_exam_value:
            value = current_exam_value.lower().strip()
            if value == "yes":
                await page.evaluate('document.getElementById("c36037f0-72fa-ed11-8f6e-00224893311a_TRUE").click();')

                # Now handle the input field
                await page.type('input[name="9d2a875b-74fa-ed11-8f6e-00224893311a"]',
                                data.get("CurrentExamDetails", ""))

            elif value == "no":
                await page.evaluate('document.getElementById("c36037f0-72fa-ed11-8f6e-00224893311a_FALSE").click();')



    try:
        await handle_tuberculosis_radio()
        await handle_renal_dialysis_radio()
        await handle_hospital_care_radio()
        await handle_residential_care_radio()
        await handle_stay_duration_dropdown()
        await handle_previous_medical_examination_radio()
        await handle_current_medical_examination_radio()
    except Exception as e:
        await delay(2)
        await handle_tuberculosis_radio()
        await handle_renal_dialysis_radio()
        await handle_hospital_care_radio()
        await handle_residential_care_radio()
        await handle_stay_duration_dropdown()
        await handle_previous_medical_examination_radio()
        await handle_current_medical_examination_radio()
        print(e)


##################


async def seventh_page(page,data):
    # Navigate to the page and wait for it to fully load
    # Navigate to the page and wait for it to fully load
    await page.wait_for_load_state(state='networkidle', timeout=120000)

    # Get employment status from data
    employment_status = data.get("AreYouCurrentlyWorking")
    # input('wai')

    print("employment_status.strip():,",employment_status.strip())

    # Check if employment status is Yes
    if employment_status.strip().title() == "Yes":
        # Select 'Yes' from the dropdown
        await page.select_option('select[name="ac83095f-0d6b-eb11-a812-000d3acb9f99_select"]',
                                 value="0a1b124f-d698-eb11-b1ac-000d3acbf832")

        # Handle the start date field
        start_date = data.get("StartDate")
        if start_date:
            # Split start date into month and year
            month, year = start_date.split("/")

            # Fill in the month
            await page.type('input[name="9fef8f94-4c67-eb11-a812-000d3a6a362f_GRP01051_000_date_mm"]', month)

            # Fill in the year
            await page.type('input[name="9fef8f94-4c67-eb11-a812-000d3a6a362f_GRP01051_000_date_yy"]', year)
            await press_enter(page)

        # Handle the role field
        role = data.get("RoleOrJobTitle")
        if role:
            await page.type('input[name="77c91af2-4c67-eb11-a812-000d3a6a362f_GRP01051_000"]', role)
            await press_enter(page)

        # Handle the country of work field
        country_of_work = data.get("CountryOfWork")
        if country_of_work:
            await page.type('input[name="3f6f0cf1-6367-eb11-a812-000d3a6a362f_GRP01051_000"]', country_of_work)
            await press_enter(page)

        # Handle the country of organisation field
        country_of_organisation = data.get("CountryOfOrganisation")
        if country_of_organisation:
            await page.type('input[name="e2e8f896-aa77-eb11-a812-000d3acbbbd8_GRP01051_000"]', country_of_organisation)
            await press_enter(page)

        # Handle the company name field
        company_name = data.get("CompanyName")
        if company_name:
            await page.type('input[name="8b206507-4d67-eb11-a812-000d3a6a362f_GRP01051_000"]', company_name)
            await press_enter(page)

        # Handle the head office address field
        head_office_address = data.get("HeadOfficeAddress")
        if head_office_address:
            await page.type('input[name="10dbcbfc-a674-eb11-a812-000d3acbbbd8_GRP01051_000_address"]',
                            head_office_address)

            # await press_enter(page)

        # Handle the employer phone number field
        employer_phone = data.get("EmployerPhoneNumber")
        if employer_phone:
            await page.type('input[name="d8ccbc49-a874-eb11-a812-000d3acbbbd8_GRP01051_000"]', employer_phone)

        # Handle the employer email address field
        employer_email = data.get("EmployerEmailAddress")
        if employer_email:
            await page.type('input[name="c9811368-a874-eb11-a812-000d3acbbbd8_GRP01051_000"]', employer_email)

    # Check if employment status is No
    elif employment_status.strip().title() == "No":
        # Select 'No' from the dropdown
        await page.select_option('select[name="ac83095f-0d6b-eb11-a812-000d3acb9f99_select"]',
                                 value="b42b0f55-d698-eb11-b1ac-000d3acbf832")

    elif employment_status.strip().title() == "Retired":
        #9127185b-d698-eb11-b1ac-000d3acbf832

        # Select 'Retired' from the dropdown
        await page.select_option('select[name="ac83095f-0d6b-eb11-a812-000d3acb9f99_select"]',
                                 value="9127185b-d698-eb11-b1ac-000d3acbf832")
        # Handle the start date field
        retired_start_date = data.get("RetiredStartDate")
        if retired_start_date:
            # Split start date into month and year
            start_month, start_year = retired_start_date.split("/")

            # Fill in the month
            await page.type('input[name="9fef8f94-4c67-eb11-a812-000d3a6a362f_GRP01051_000_date_mm"]',
                            start_month)

            # Fill in the year
            await page.type('input[name="9fef8f94-4c67-eb11-a812-000d3a6a362f_GRP01051_000_date_yy"]',
                            start_year)

            await press_enter(page)

        # Handle the end date field
        retired_end_date = data.get("RetiredEndDate")
        if retired_end_date:
            # Split end date into month and year
            end_month, end_year = retired_end_date.split("/")

            # Fill in the month
            await page.type('input[name="2537e9b3-4c67-eb11-a812-000d3a6a362f_GRP01051_000_date_mm"]',
                            end_month)

            # Fill in the year
            await page.type('input[name="2537e9b3-4c67-eb11-a812-000d3a6a362f_GRP01051_000_date_yy"]', end_year)
            await press_enter(page)

        # Handle the role or job title field
        role_title = data.get("RetiredRoleTitle")
        if role_title:
            await page.type('input[name="77c91af2-4c67-eb11-a812-000d3a6a362f_GRP01051_000"]', role_title)
            await press_enter(page)

        # Handle the country or territory of work field
        country_work = data.get("RetiredCountryOfWork")
        if country_work:
            await page.type('input[name="3f6f0cf1-6367-eb11-a812-000d3a6a362f_GRP01051_000"]', country_work)
            await press_enter(page)

        # Handle the country or territory where organisation is based field
        country_organisation = data.get("RetiredCountryOfOrganisation")
        if country_organisation:
            await page.type('input[name="e2e8f896-aa77-eb11-a812-000d3acbbbd8_GRP01051_000"]',
                            country_organisation)
            await press_enter(page)

        # Handle the name of organisation or employer field
        employer_name = data.get("RetiredEmployerName")
        if employer_name:
            await page.type('input[name="8b206507-4d67-eb11-a812-000d3a6a362f_GRP01051_000"]', employer_name)

            await press_enter(page)

        # Handle the address field
        address = data.get("RetiredHeadOfficeAddress")
        if address:
            await page.type('input[name="10dbcbfc-a674-eb11-a812-000d3acbbbd8_GRP01051_000_address"]', address)
            # await press_enter(page)


        # Handle the employer phone number field
        employer_phone = data.get("RetiredEmployerPhoneNumber")
        if employer_phone:
            await page.type('input[name="d8ccbc49-a874-eb11-a812-000d3acbbbd8_GRP01051_000"]', employer_phone)

        # Handle the employer email address field
        employer_email = data.get("RetiredEmployerEmailAddress")
        if employer_email:
            await page.type('input[name="c9811368-a874-eb11-a812-000d3acbbbd8_GRP01051_000"]', employer_email)


async def Eight_page(page, data):
    # Navigate to the page and wait for it to fully load
    # Navigate to the page and wait for it to fully load
    await page.wait_for_load_state(state='networkidle', timeout=120000)
    async def handle_select(select_id, option_value):
        await page.select_option(f'select[name="{select_id}"]', value=option_value)

    async def handle_marital_status():
        marital_status = data.get("MaritalStatus")

        if marital_status:
            marital_status_map = {
                "Single": "29bd6bec-2698-eb11-b1ac-000d3acbff6e",
                "Married": "2bbd6bec-2698-eb11-b1ac-000d3acbff6e",
                "Partner": "2dbd6bec-2698-eb11-b1ac-000d3acbff6e",
                "Engaged": "2fbd6bec-2698-eb11-b1ac-000d3acbff6e",
                "Separated": "31bd6bec-2698-eb11-b1ac-000d3acbff6e",
                "Divorced": "33bd6bec-2698-eb11-b1ac-000d3acbff6e",
                "Widowed": "35bd6bec-2698-eb11-b1ac-000d3acbff6e"
            }

            if marital_status in marital_status_map:
                await handle_select("40059b40-a96c-eb11-a812-000d3acb9f99_select", marital_status_map[marital_status])

    async def handle_current_partner():
        current_partner = data.get("current_partner")  # or "No" depending on your logic

        # Evaluate JavaScript to click Yes or No
        await page.evaluate(f'''(yes_or_no) => {{
              const radioButton = document.getElementById('548e60a5-ae6c-eb11-a812-000d3acb9f99_' + (yes_or_no === "yes" ? "TRUE" : "FALSE"));
              radioButton.click();
          }}''', current_partner.lower().strip())



    async def handle_yes_or_no():
        yes_or_no = data.get("YesOrNo")

        print(yes_or_no)

        if yes_or_no:
            if yes_or_no.lower().strip() == "yes":
                await page.evaluate('''() => {
                    document.getElementById('f91a804f-fa6e-eb11-a812-000d3acba81e_TRUE').click();
                }''')


                contact_first_name = data.get("ContactFirstName", "")
                contact_middle_names = data.get("ContactMiddleNames", "")
                contact_surname = data.get("ContactSurname", "")
                relationship_type = data.get("RelationshipType", "")

                relationship_mapping = {
                    "Family": "ca763f88-de85-eb11-a812-000d3acbea15",
                    "Friend": "8a0d9b8f-de85-eb11-a812-000d3acbea15",
                    "Other": "900d9b8f-de85-eb11-a812-000d3acbea15"
                }

                relationship_option_value = relationship_mapping.get(relationship_type, "")

                # Typing the contact first name
                await page.evaluate('''(contact_first_name) => {
                    document.getElementById('ff4c5181-fa6e-eb11-a812-000d3acba81e_GRP01021_000').value = contact_first_name;
                }''', contact_first_name)

                # Typing the contact middle names
                await page.evaluate('''(contact_middle_names) => {
                    document.getElementById('33281a8f-fa6e-eb11-a812-000d3acba81e_GRP01021_000').value = contact_middle_names;
                }''', contact_middle_names)

                # Typing the contact surname
                await page.evaluate('''(contact_surname) => {
                    document.getElementById('51268403-7796-eb11-b1ac-000d3acbf832_GRP01021_000').value = contact_surname;
                }''', contact_surname)

                # Selecting the relationship option
                await page.evaluate('''(relationship_option_value) => {
                    const selectElement = document.getElementById('783a15d2-fa6e-eb11-a812-000d3acba81e_GRP01021_000_select');
                    selectElement.value = relationship_option_value;
                    selectElement.dispatchEvent(new Event('change', { bubbles: true }));
                }''', relationship_option_value)



                # Inserting additional HTML snippet for contact's date of birth
                dob = data.get("ContactDOB", "")
                if dob:
                    dob_day, dob_month, dob_year = dob.split("/")

                    await page.evaluate('''(dob_day) => {
                        document.getElementById('0149b340-7896-eb11-b1ac-000d3acbf832_GRP01021_000_date_dd').value = dob_day;
                    }''', dob_day)

                    await page.evaluate('''(dob_month) => {
                        document.getElementById('0149b340-7896-eb11-b1ac-000d3acbf832_GRP01021_000_date_mm').value = dob_month;
                    }''', dob_month)

                    # For the input with class "mcs-date-field" and ID "0149b340-7896-eb11-b1ac-000d3acbf832_GRP01021_000_date_yy"
                    await page.type('//input[@id="0149b340-7896-eb11-b1ac-000d3acbf832_GRP01021_000_date_yy"]', dob_year)
                    await press_enter(page)


                    # await page.evaluate('''(dob_year) => {
                    #     document.getElementById('0149b340-7896-eb11-b1ac-000d3acbf832_GRP01021_000_date_yy').value = dob_year;
                    # }''', dob_year)


            elif yes_or_no.lower().strip() == "no":
                # Simulate clicking the "No" option
                await page.evaluate('''() => {
                    document.getElementById('f91a804f-fa6e-eb11-a812-000d3acba81e_FALSE').click();
                }''')
                pass

    async def handle_contact_details():
        # Handle contact number
        contact_number = data.get("ContactNumber", "")
        if contact_number:
            await page.evaluate('''(contact_number) => {
                document.getElementById('3955c11e-fb6e-eb11-a812-000d3acba81e_GRP01021_000').value = contact_number;
            }''', contact_number)

        # Handle email address
        email_address = data.get("EmailAddress", "")
        if email_address:
            await page.evaluate('''(email_address) => {
                document.getElementById('28f97371-fb6e-eb11-a812-000d3acba81e_GRP01021_000').value = email_address;
            }''', email_address)

        # Inserting additional HTML snippet for address
        address = data.get("AddressContact", "")
        if address:
            # For the input with class "form-control" and name "a5e444ed-fa6e-eb11-a812-000d3acba81e_GRP01021_000_address"
            await page.type('input.form-control[name="a5e444ed-fa6e-eb11-a812-000d3acba81e_GRP01021_000_address"]',
                            address)

            await press_enter(page)

            # await page.evaluate('''(address) => {
            #     document.getElementById('a5e444ed-fa6e-eb11-a812-000d3acba81e_GRP01021_000_address').value = address;
            # }''', address)

    try:
        # Call the function to handle marital status select element
        await handle_marital_status()

        await handle_current_partner()
        # Call the function to handle yes or no selection
        await handle_yes_or_no()
        # Call the function to handle contact details
        await handle_contact_details()
    except Exception as e:
        print(e)
        await delay(2)
        # Call the function to handle marital status select element
        await handle_marital_status()

        await handle_current_partner()
        # Call the function to handle yes or no selection
        await handle_yes_or_no()
        # Call the function to handle contact details
        await handle_contact_details()





async def Nineth_page(page, data):
    # Navigate to the page and wait for it to fully load
    # Navigate to the page and wait for it to fully load
    await page.wait_for_load_state(state='networkidle', timeout=120000)
    async def handle_yes_or_no():
        choice = data.get("IM_yes_or_no_choice", "")  # Get the choice from data
        if choice.lower() == "yes":
            await page.evaluate('''() => {
                document.getElementById('6d9e8968-556a-eb11-a812-000d3acb9f99_TRUE').click();
            }''')

            await select_capacity()

            # Handle personal details
            await handle_personal_details()

            # Handle email correspondence
            await handle_email_correspondence()




        elif choice.lower() == "no":
            await page.evaluate('''() => {
                document.getElementById('6d9e8968-556a-eb11-a812-000d3acb9f99_FALSE').click();
            }''')

    async def select_capacity():
        capacity = data.get("IM_capacity_option", "")  # Get the capacity option from data
        await page.evaluate(f'''(capacity) => {{
            const select = document.getElementById('367f1795-556a-eb11-a812-000d3acb9f99_GRP01070_000_select');
            const options = select.getElementsByTagName('option');
            for (let option of options) {{
                if (option.text === capacity) {{
                    option.selected = true;
                    select.dispatchEvent(new Event('change', {{ bubbles: true }}));
                    break;
                }}
            }}
        }}''', capacity)

    async def handle_personal_details():
        first_name = data.get("IM_first_name", "")
        surname = data.get("IM_surname", "")
        company_name = data.get("IM_company_name", "")
        country = data.get("IM_country", "")
        email = data.get("IM_email", "")
        contact_number = data.get("IM_contact_number", "")
        adviser_number = data.get("IM_adviser_number")

    #     # Fill in the Adviser Number
    #     await page.evaluate('''(adviser_number) => {
    #     const input = document.querySelector('input[name="eb5a44a5-5d6a-eb11-a812-000d3acb9f99_GRP01070_000"]');
    #     input.value = adviser_number;
    #     input.dispatchEvent(new Event('input', { bubbles: true }));
    # }''', adviser_number)

        await page.focus('input[name="eb5a44a5-5d6a-eb11-a812-000d3acb9f99_GRP01070_000"]')  # Focus on the input field
        await page.keyboard.type(adviser_number)  # Type the adviser number
        await page.keyboard.press('Enter')

        await press_enter(page)
        await page.focus('input[name="eb5a44a5-5d6a-eb11-a812-000d3acb9f99_GRP01070_000"]')  # Focus on the input field
        await page.keyboard.type(adviser_number)  # Type the adviser number
        await page.keyboard.press('Enter')

        await press_enter(page)

       # Fill in the email
        await page.evaluate(f'''(email) => {{
            document.querySelector('input[name="0f388904-0af0-eb11-94ef-000d3acbf60b_GRP01070_000"]').value = email;
        }}''', email)


        # Fill in the contact number
        await page.evaluate(f'''(contact_number) => {{
               document.querySelector('input[name="7018b6f0-0af0-eb11-94ef-000d3acbf60b_GRP01070_000"]').value = contact_number;
           }}''', contact_number)

        # # Fill in the first name
        # await page.evaluate(f'''(first_name) => {{
        #     document.querySelector('input[name="98ee3815-566a-eb11-a812-000d3acb9f99_GRP01070_000"]').value = first_name;
        # }}''', first_name)
        #
        # # Fill in the surname
        # await page.evaluate(f'''(surname) => {{
        #     document.querySelector('input[name="63e04123-566a-eb11-a812-000d3acb9f99_GRP01070_000"]').value = surname;
        # }}''', surname)
        #
        # # Fill in the company name
        # await page.evaluate(f'''(company_name) => {{
        #     document.querySelector('input[name="3d907143-566a-eb11-a812-000d3acb9f99_GRP01070_000"]').value = company_name;
        # }}''', company_name)
        #
        # # Fill in the country
        # await page.type('input[name="a3943af5-576a-eb11-a812-000d3acb9f99_GRP01070_000"]', country)
        #
        # # Fill in the email
        # await page.evaluate(f'''(email) => {{
        #     document.querySelector('input[name="45698ade-5c6a-eb11-a812-000d3acb9f99_GRP01070_000"]').value = email;
        # }}''', email)
        #
        # # Fill in the contact number
        # await page.evaluate(f'''(contact_number) => {{
        #     document.querySelector('input[name="c71c2da1-5c6a-eb11-a812-000d3acb9f99_GRP01070_000"]').value = contact_number;
        # }}''', contact_number)

    async def handle_email_correspondence(): # License Immigrant
        correspondence_choice = data.get("IM_email_correspondence_choice", "")  # Get the choice from data
        if correspondence_choice.lower() == "yes":
            await page.evaluate('''() => {
                document.getElementById('9b03b481-0af0-eb11-94ef-000d3acbf60b_GRP01070_000_TRUE').click();
            }''')
        elif correspondence_choice.lower() == "no":
            await page.evaluate('''() => {
                document.getElementById('9b03b481-0af0-eb11-94ef-000d3acbf60b_GRP01070_000_FALSE').click();
            }''')

    async def fill_advice_provided():
        advice_provided = data.get('IM_Advice_provided','yes')

        if advice_provided.lower() =='yes':
            advice_provided ='true'
        else:
            advice_provided = 'false'
        script = f'''
        () => {{
            const trueRadio = document.getElementById('8aebc441-606a-eb11-a812-000d3acb9f99_GRP01071_000_TRUE');
            const falseRadio = document.getElementById('8aebc441-606a-eb11-a812-000d3acb9f99_GRP01071_000_FALSE');

            if ({advice_provided}) {{
                trueRadio.click();
            }} else {{
                falseRadio.click();
            }}
        }}'''

        await page.evaluate(script)

    try:

        # Call handle_yes_or_no and select_capacity functions
        await handle_yes_or_no()

        await fill_advice_provided()

    except Exception as e:
       print(e)
       await delay(5)
       # Call handle_yes_or_no and select_capacity functions
       await handle_yes_or_no()

       await fill_advice_provided()





async def click_save_and_continue_button(page):
    await page.click('input#questionsubmit', delay=1000)







async def handle_notification_banner(page):
    error_message = await page.evaluate('''() => {
        const banner = document.querySelector('#notification_banner');
        if (banner) {
            const errorMessageElement = banner.querySelector('.body ul');
            if (errorMessageElement) {
                const errorMessage = errorMessageElement.innerText.trim();
                return errorMessage;
            }
        }
        return null;
    }''')
    return error_message

async def is_error_page(page, update, bot, error_message=None):

    if error_message:
        print("Error Detected:", error_message)
        recent_message = await bot.message.reply_text(
            f"‼️The following errors have occurred:\n\n{error_message}\n\nPlease Reply with 'Yes' or 'No' once you are done to proceed",
            reply_to_message_id=bot.message.message_id)

        while True:
            state = load_json()  # Load JSON data inside the loop to get the most recent state
            if state.get("user_confirmed"):
                new_data = {"user_confirmed": False}
                save_json(new_data)
                break  # Exit the loop if user_confirmed is True
            await asyncio.sleep(1)
        return recent_message
    else:
        # Continue with the next steps
        await update.edit_text("No errors detected. Clicking Next button.........")

        await click_save_and_continue_button(page)

        await asyncio.sleep(0.5)
        await page.wait_for_load_state("domcontentloaded")



async def handle_next_button_page2(page, update, bot, tag=None, mode='2'):



    if mode=='2':
        is_button_visible = await page.is_visible(tag)
        if not is_button_visible:
            await bot.message.reply_text(
                "The button to start the application is not visible. Please check and complete any missing values.\n\nPress 'Yes' after completing the missing values to continue.")


    while True:
        await delay(1)
        is_button_visible = await page.is_visible(tag)
        if not is_button_visible:
            state = load_json()
            if state.get("user_confirmed"):
                new_data = {"user_confirmed": False}
                save_json(new_data)

                await update.edit_text("Clicking Next button.........")
                await page.click(tag)

                await asyncio.sleep(0.5)
                await page.wait_for_load_state("domcontentloaded")

                break
        else:
            await handle_manual_control(page, bot, mode=tag)
            # await page.click(tag)
            await page.wait_for_load_state("domcontentloaded")
            break


async def handle_manual_control(page, bot, mode=None):
    if bot_manual_setting:
        # await update.edit_text("Do you want to continue to next page? Reply with 'Yes' or 'No'")
        recent_message = await bot.message.reply_text("Do you want to continue to next page? Reply with 'Yes' or 'No'",
                                                      reply_to_message_id=bot.message.message_id)

        while True:
            state = load_json()  # Load JSON data inside the loop to get the most recent state
            if state.get("user_confirmed"):
                new_data = {"user_confirmed": False}
                save_json(new_data)

                if mode:
                    await page.click(mode)

                else:
                    await click_save_and_continue_button(page)  # click next page
                    pass

                await asyncio.sleep(0.5)


                break  # Exit the loop if user_confirmed is True

            await asyncio.sleep(1)
        return recent_message

    else:
        if mode:
            await page.click(mode)

        else:
            await click_save_and_continue_button(page)  # click next page
            pass


async def handle_next_button(page, update, bot):

    await handle_manual_control(page,bot)

    while True:
        await delay(1)

        is_warning = await handle_warning(page, bot)  # handle the warning to proceed

        if is_warning:
            await page.wait_for_load_state(state='networkidle')
            print(is_warning, 'is_warning')
            await delay(15)
            break
        else:
            error_message = await handle_notification_banner(page)
            if error_message:
                recent_message = await is_error_page(page, update, bot, error_message=error_message)
                # check error message
                await click_save_and_continue_button(page)
                await page.wait_for_load_state("domcontentloaded")
            else:
                await page.wait_for_load_state("domcontentloaded")
                break





async def main(update=None, bot=None):
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False, slow_mo=1000)
            context = await browser.new_context()
            page = await context.new_page()

            await page.goto("https://apply.immigration.govt.nz/visa_dashboard/")

            with open("data.csv", "r") as csv_file:
                reader = csv.reader(csv_file)
                data = next(reader)
                data = transform_data(list(reader))


#### Handle Login Pga buton ###############
            await login_page(update, page, data, bot)
            recent_message = await click_next_page(update, bot, page, mode='login')
            if recent_message:
                update = recent_message
            await delay(2)

            # Navigate to the page and wait for it to fully load
            await page.wait_for_load_state(state='networkidle', timeout=120000)



            # -- Next page --- ###
            try:
                await first_page(update, page, data)

            except:
                pass

            await handle_next_button_page2(page, update, bot,tag='input[type="button"][name="questionsubmit"]')


            ## -- Second page -- ###
            try:
                await second_page(update,page,data)

            except:
                await delay(5)
                await second_page(update, page, data)

            ## -- Next page -- #
            try:

                await third_page(update,page,data)
            except:
                await delay(5)
                await third_page(update, page, data)

            await handle_next_button(page,update,bot)



            ## -- Next page -- #
            try:
                await fourth_page(page, data)
            except:
                await delay(5)
                await fourth_page(page, data)
            await handle_next_button(page, update, bot)

            ## -- Next page -- #
            try:
                await fifth_page(page,data)
            except:
                await delay(5)
                await fifth_page(page, data)

            await handle_next_button(page, update, bot)

            ## -- Next page -- #
            try:
                await sixth_page(page, data)
            except:
                await delay(5)
                await sixth_page(page, data)

            await handle_next_button(page, update, bot)

            ## -- Next page -- #
            try:

                await seventh_page(page, data)
            except:
                await delay(5)

                await seventh_page(page, data)

            await handle_next_button(page, update, bot)

            ## -- Next page -- #
            try:
                await Eight_page(page, data)
            except:
                await delay(5)
                await Eight_page(page, data)
            await handle_next_button(page, update, bot)

            ## -- Next page -- #
            try:
                await Nineth_page(page, data)
            except:
                await Nineth_page(page, data)
            await handle_next_button(page, update, bot)

            await bot.message.reply_text(
                "Thank you i am Done ! please Upload the necessary docs and use 'stop or s' or  CTRL + C to Close me",
                reply_to_message_id=bot.message.message_id)


            await delay(300000)
            await bot.message.reply_text(
                "Thank you i am Done ! am shuttung down now goood bye",
                reply_to_message_id=bot.message.message_id)

            await browser.close()



            # await browser.close()







    except Exception as e:
        new_data = {"is_launched": False, "user_confirmed": False}
        save_json(new_data)
        recent_message = await bot.message.reply_text(
            f"There is an error: {e}\npossibly your internet make sure your internet is good\nPlease restart with 'y' '",
            reply_to_message_id=bot.message.message_id)
        import traceback
        traceback.print_exc()

    except SystemExit as e:
        new_data = {"is_launched": False, "user_confirmed": False}
        save_json(new_data)
        print("HIII save by force ")

    finally:
        new_data = {"is_launched": False, "user_confirmed": False}
        save_json(new_data)
        print("HIII save by finally this is for the reason! ")
