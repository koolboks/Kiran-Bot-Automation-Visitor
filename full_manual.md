# Instructions for Bot Commands

1. **Toggle Manual Mode (toggle_manual)**:
   - **Purpose**: Switches the bot between manual and automatic modes.
   - **What it does**:
     - If in manual mode, the bot will wait for user confirmation before proceeding with each step.
     - If in automatic mode, the bot will make decisions and proceed without requiring user input.
   - **How to use**: Click on the "Manual" button. The button label will change to "Manual ✅" (enabled) or "Manual ❌" (disabled).

2. **Toggle Wizard Mode (wizard)**:
   - **Purpose**: Enables or disables the wizard mode.
   - **What it does**:
     - When enabled, the wizard will handle pop-ups and proceed automatically.
   - **How to use**: Click on the "Wizard" button. The button label will change to "Wizard ✅" (enabled) or "Wizard ❌" (disabled).

3. **Toggle Preview Mode (toggle_preview)**:
   - **Purpose**: Switches the preview mode on or off.
   - **What it does**:
     - If enabled, you will be able to preview steps before they are executed.
   - **How to use**: Click on the "Preview" button. The button label will change to "Preview ✅" (enabled) or "Preview ❌" (disabled).

4. **Select Browser (select_browser)**:
   - **Purpose**: Allows the user to select which browser to use for the form-filling process.
   - **What it does**:
     - Presents options to choose from different browsers like Firefox, Chrome, or Webkit.
   - **How to use**: Click on the "Select Browser" button and then choose the desired browser from the provided options.

5. **Upload Data (upload_data)**:
   - **Purpose**: Allows the user to upload data required for the form-filling process.
   - **What it does**:
     - Prompts the user to upload a data file (e.g., data.csv).
   - **How to use**: Click on the "Upload Data" button and follow the instructions to upload your data file.

6. **Launch Form Filling (start_form_filling)**:
   - **Purpose**: Starts the form-filling process.
   - **What it does**:
     - Initiates the script to begin filling out forms based on the provided data.
     - Prompts the user to confirm the launch by replying with 'Y' to start or 'N' to cancel.
   - **How to use**: Click on the "Launch" button to start the process. Confirm the action when prompted.

7. **Message Handler (message_handler)**:
   - **Purpose**: Handles various types of messages from the user, including file uploads and text commands.
   - **What it does**:
     - Processes CSV file uploads and saves them as "data.csv".
     - Handles specific text commands:
       - 'y': Launches the form-filling process.
       - 'force': Clears cache and restores browser.
       - 'ok': Proceeds after a 12-second delay.
       - 'never': Closes pop-ups.
       - 'yes': Confirms the user’s action.
       - 'no' or "NO": Waits for the user's confirmation.
       - 'stop' or 's' or 'S' or "STOP": Stops/restarts the Chrome browser and running task and prompts to relaunch. This is useful when you want to upload a new data.csv file.
   - **How to use**: Upload a CSV file or send text commands as described. Please note that logic to handle all CSVs has been added and be mindful not to edit other columns except the value column. Avoid adding commas in other columns.

# How to Run the Whole Script

1. **Ensure All Settings are Correct**:
   - Run the bash file with a single click: `run_script.sh`.
   - To restart the app, use "stop" in the message box. There is no need to use CTRL + C unless you want to terminate it finally.
   - Make sure all necessary settings (Manual, Preview, Wizard) are configured as per your needs.
   - Use the respective buttons to toggle these settings.

2. **Select the Browser**:
   - (This feature is not available now; just use the default browser)
   - Click on the "Select Browser" button and choose the browser you want to use.

3. **Upload Data**:
   - Click on the "Upload Data" button and upload the necessary file or just drag and drop it there. Once you are done with one user, you can add another user, etc.

4. **Start the Form Filling**:
   - Click on the "Launch" button to start the process.
   - Respond with 'Y' to confirm and start the process or 'N' to cancel it.

By following these instructions, you can effectively use the bot's features and ensure the script runs smoothly from start to finish.

Lastly, I recommend first using the WIZARD mode to see how it works effectively! and be modified that Wizard mode is only available on Visitor visa 😎
