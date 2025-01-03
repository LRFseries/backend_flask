
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import ratemyprofessor as rmp
import json
import os
import requests
from bs4 import BeautifulSoup
import time
from groq import Groq
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import re
from collections import deque
from dotenv import load_dotenv

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
memory = deque(maxlen=15)

# Define your Python functions
load_dotenv('api_key.env')
os.environ["GROQ_API_KEY"] = os.getenv('groq_api_key')


def get_professor_id(name):
    """
    Get the Rate My Professors ID of a professor by their name and school.

    Args:
        name (str): Full name of the professor.

    Returns:
        str: Professor ID if found, otherwise None.
    """
    base_url = "https://www.ratemyprofessors.com/search/professors/1011"
    query = f"{name}"
    params = {
        "q": query
    }

    # Send search request
    response = requests.get(base_url, params=params)
    if response.status_code != 200:
        print("Failed to fetch the page")
        return None

    soup = BeautifulSoup(response.text, 'html.parser')

    # Find professor profile links
    professor_links = soup.select('a[href*="/professor/"]')
    if not professor_links:
        print("No professors found.")
        return None

    # Extract the first valid professor ID
    for link in professor_links:
        href = link.get("href")
        if "/professor/" in href:
            professor_id = href.split("/")[-1]
            return professor_id

    print("Professor ID not found.")
    return None



def getProfessorReviews(id):
    user_tags = []
    user_reviews = []
    url = f'https://www.ratemyprofessors.com/professor/{id}'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise error for HTTP issues
        soup = BeautifulSoup(response.content, 'html.parser')

        # Extract reviews
        review_blocks = soup.find_all('div', class_='Rating__RatingBody-sc-1rhvpxz-0')
        for i, review_block in enumerate(review_blocks, start=1):
            user_review = review_block.find('div', class_='Comments__StyledComments-dzzyvm-0')
            user_reviews.append(user_review.get_text(strip=True) if user_review else "No review text available")

        # Extract tags
        tags = soup.find_all('span', class_='Tag-bs9vf4-0')
        user_tags = [tag.get_text(strip=True) for tag in tags]

    except requests.exceptions.RequestException as e:
        return {"error": f"Failed to fetch reviews: {e}"}

    return {
        "reviews": user_reviews if user_reviews else ["No reviews available"],
        "tags": user_tags if user_tags else ["No tags available"]
    }



import nltk

def getProfessor(expression):
    """Fetch information from a certain professor at Texas Tech"""
    school = rmp.get_school_by_name("Texas Tech University")

    professors = rmp.get_professors_by_school_and_name(school, f"{expression}")

    try:
        professor = professors[0]
        most_similar_professor = professors[0]
        most_similar_name = professors[0].name
        most_similar_distance = nltk.edit_distance(most_similar_name, expression)

        for professor in professors[1:]:
            if(nltk.edit_distance(expression, professor.name) < most_similar_distance):
                most_similar_distance = nltk.edit_distance(expression, professor.name)
                most_similar_name = professor.name
                most_similar_professor = professor
    except:
        return("Error retrieving professor data! Please try again")




    user_reviews = getProfessorReviews(get_professor_id(f"{most_similar_name}"))
    professor.reviews = user_reviews
    if professor is not None:
      return json.dumps({"professor name": most_similar_professor.name,
                         "professor department": most_similar_professor.department,
                         "professor school": most_similar_professor.school.name,
                         "professor rating": most_similar_professor.rating,
                         "professor difficulty": most_similar_professor.difficulty,
                         "professor num_ratings": most_similar_professor.num_ratings,
                         "professor reviews": professor.reviews})

    else:
      return json.dumps({"error": "Invalid expression"})

allDepartments ={
  1950: 'Academic advisement',
  1: 'Accounting',
  85: 'Advertising',
  2: 'Agriculture',
  3: 'Anthropology',
  1868: 'Applied studies',
  4: 'Architecture',
  113: 'Art',
  5: 'Art history',
  1421: 'Atmospheric sciences',
  6: 'Biology',
  7: 'Business',
  61: 'Chemical Engineering',
  8: 'Chemistry',
  9: 'Classics',
  10: 'Communication',
  11: 'Computer Science',
  12: 'Criminal Justice',
  13: 'Culinary Arts',
  14: 'Design',
  15: 'Economics',
  16: 'Education',
  17: 'Engineering',
  18: 'English',
  19: 'Ethnic Studies',
  106: 'Exercise and Sport Science',
  20: 'Film',
  21: 'Finance',
  22: 'Fine Arts',
  23: 'Geography',
  24: 'Geology',
  25: 'Graphic Arts',
  26: 'Health Science',
  27: 'History',
  118: 'Honors',
  28: 'Hospitality',
  1584: 'Human Dev and Family Sciences',
  29: 'Humanities',
  30: 'Information Science',
  2631: 'Integrative Studies',
  135: 'International Studies',
  32: 'Journalism',
  333: 'Kinesiology',
  2647: 'Landscape Architecture',
  33: 'Languages',
  34: 'Law',
  35: 'Literature',
  36: 'Management',
  37: 'Marketing',
  38: 'Mathematics',
  1396: 'Mathematics and Statistics',
  39: 'Medicince',
  134: 'Microbiology',
  1244: 'Modern and Classical Lang and Lit.',
  40: 'Music',
  41: 'Nursing',
  2727: 'Nutritional Sciences',
  1772: 'Petroleum Engineering',
  42: 'Philosophy',
  43: 'Physical Education',
  44: 'Physics',
  45: 'Political Science',
  46: 'Psychology',
  48: 'Science',
  49: 'Social Science',
  50: 'Social Work',
  51: 'Sociology',
  731: 'Technology',
  52: 'Theater',
  53: "Women's Studies",
  54: 'Writing'
}


def searchDepartment(expression):

    print("Running search department tool with expression:", expression)
    most_similar_department = allDepartments[1]
    most_similar_distance = nltk.edit_distance(most_similar_department, expression)

    for department in allDepartments.values():  # Iterate over all values in the dictionary
        if nltk.edit_distance(expression, department) < most_similar_distance:
            most_similar_distance = nltk.edit_distance(expression, department)
            most_similar_department = department

    if(most_similar_distance > 10): #if the name is wildly different from any department throw error
        return(f"Could not find department. Please try again. Here is a list of all available departments:  + {allDepartments.values()}")

    for key, value in allDepartments.items(): # match most similar department name to its URL ID
        if value == most_similar_department:
            departmentID = key


    url = f'https://www.ratemyprofessors.com/search/professors/1011?q=*&did={departmentID}'
    # Specify the path to the ChromeDriver executable
    driver_path = r'C:\Users\lrfar\.cache\selenium\chromedriver\win64\131.0.6778.204\chromedriver.exe'  # Update this to the correct path

    # Initialize the ChromeDriver service
    service = Service(driver_path)

    # Set Chrome options
    options = webdriver.ChromeOptions()
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--ignore-ssl-errors')
    options.add_argument("log-level=3")
    options.add_argument('--headless')  # Run Chrome in headless mode
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-extensions')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--no-sandbox')
    options.add_argument('--enable-unsafe-swiftshader')
    prefs = {"profile.managed_default_content_settings.images": 2, "profile.managed_default_content_settings.stylesheets": 2}
    options.add_experimental_option("prefs", prefs)

    professors_in_department = {}

    # Initialize the browser
    browser = webdriver.Chrome(service=service, options=options)

    # Open the URL
    browser.get(url)

    try:
        # Use explicit wait instead of time.sleep()
        WebDriverWait(browser, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'a.TeacherCard__StyledTeacherCard-syjs0d-0.dLJIlx'))
        )

        x1 = browser.find_elements(By.CSS_SELECTOR, 'a.TeacherCard__StyledTeacherCard-syjs0d-0.dLJIlx')
        # Print the text of each element
        for element in x1[:4]:
            # Split data into lines
            lines = element.text.splitlines()
            name = lines[3].strip()  # Index 3 because name on line 4
            # print("Name:", name)
            # print("Element: ", element.text)
            link = element.get_attribute("href")
            match = re.search(r'/professor/(\d+)$', link)
            if match:
                id = match.group(1)
                reviews = getProfessorReviews(id)
                professors_in_department[name] = {
                    "name": name,
                    "ratings":  element.text,
                    "reviews":  reviews,
                }

        return professors_in_department
    except Exception as e:
        print(f"An error occurred: {e}")

    finally:
        # Close the browser
        browser.quit()


from groq import Groq
import json

# Initialize the Groq client
client = Groq()
# Specify the model to be used (we recommend our fine-tuned models or the Llama 3.1 models)
MODEL = 'llama-3.1-8b-instant'


def run_conversation(user_prompt):
    # Initialize the conversation with system and user messages
    global memory


    context = ""
    for entry in memory:
        context += f"User: {entry['query']}\nAssistant: {entry['response']}\n"

    messages = [
        {
            "role": "system",
            "content": (
               f"Here is the conversation history between you and the user so far: {context}\n"
                 "You are a student assistant bot for Texas tech. You  search for names of professors "
                "given by the user and provide advice based on Rate My Professor data. "
                "When you retrieve data about a professor, summarize it in a concise, conversational manner. "
                "Highlight key details such as their ratings, difficulty, and representative reviews."
                "If professor not provided then answer question given"
                "Do not provide any information about a professor if not asked"
                "If you are not asked anything about a professor, then dont give any information, just answer the question"
                "Give information in these section and space it out: Rating ; Difficulty ; Reviews ; Tips on how to succeed in the class(make it paragraphs in between & - instead of **)"
                "When the user is asking about a department, omit the word 'department' from your tool call."
                "If the user says the word 'math' in their message, extend the word to 'mathematics' if using it in a tool"

            )
        },
        {"role": "user", "content": user_prompt}
    ]

    tools = [
        {
            "type": "function",
            "function": {
                "name": "getProfessor",
                "description": "Fetch information about a professor at Texas Tech, such as their ratings and student reviews.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "expression": {
                            "type": "string",
                            "description": "The name of the professor",
                        }
                    },
                    "required": ["expression"],
                },
            },
        },


        {
            "type": "function",
            "function": {
                "name": "searchDepartment",
                "description": "Fetch information about professors and their reviews within a certain department at Texas Tech",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "expression": {
                            "type": "string",
                            "description": "The name of the department",
                        }
                    },
                    "required": ["expression"],
                },
            },
        },


    ]

    # Make the initial API call to Groq
    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        stream=False,
        tools=tools,
        tool_choice="auto",
        max_tokens=4096
    )

    response_message = response.choices[0].message
    tool_calls = response_message.tool_calls

    if tool_calls:
        available_functions = {
            "getProfessor": getProfessor,
            "searchDepartment": searchDepartment
        }

        # Process each tool call
        for tool_call in tool_calls:
            function_name = tool_call.function.name
            function_to_call = available_functions[function_name]
            function_args = json.loads(tool_call.function.arguments)
            function_response = function_to_call(expression=function_args.get("expression"))

            # Append the professor data to the conversation for summarization
            messages.append(
                {
                    "role": "assistant",
                    "content": f"Raw professor data: {function_response}"
                }
            )

            # Add a user-like prompt asking the LLM to summarize the data
            messages.append(
                {
                    "role": "user",
                    "content": "Please summarize this data in a concise, conversational manner."
                }
            )

            # Make a second API call to get the summary
            summary_response = client.chat.completions.create(
                model=MODEL,
                messages=messages,
                stream=False,
                max_tokens=4096
            )

            memory.append({"query": user_prompt, "response": summary_response.choices[0].message.content})

            # Return the summary generated by the LLM
            return summary_response.choices[0].message.content

    # If no tool calls, return the original LLM response
    memory.append({"query": user_prompt, "response": response_message.content})

    return response_message.content if response_message.content else "I couldn't process your request. Please try again."

def run_LLM(user_input):
    return run_conversation(user_input)

# API route to call the function
@app.route('/runai', methods=['POST'])
def runai():
    data = request.json  # Get JSON data from the request
    user_input = data.get('userInput')  # Extract userInput
    if not user_input:
        return jsonify({'error': 'userInput is required'}), 400

    result = run_LLM(user_input)  # Call the Python function

    return jsonify({'message': result})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
