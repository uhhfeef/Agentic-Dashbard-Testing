from openai import OpenAI
from dotenv import load_dotenv
import os
import prompts
import sqlite3

load_dotenv()
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

iteration_history = []

def table_schema():
    conn = sqlite3.connect('data/edtech.db')
    cursor = conn.cursor()
    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table';")
    table_schema = cursor.fetchall()
    conn.close()
    return table_schema

table_schema_str = str(table_schema())

def execute_sql_query(sql_query):
    conn = sqlite3.connect('data/edtech.db')
    cursor = conn.cursor()
    cursor.execute(sql_query)
    result = cursor.fetchall()
    conn.close()
    return result

def parse_response(response_content):
    # Initialize variables for the current loop response
    thought = ""
    action = ""
    action_input = ""
    final_answer = ""

    if "Thought:" in response_content:
        thought = response_content.split("Thought:")[1].split("Action:")[0].strip()
    if "Action:" in response_content:
        action = response_content.split("Action:")[1].split("Action Input:")[0].strip()
    if "Action Input:" in response_content:
        action_input = response_content.split("Action Input:")[1].split("Final Answer:")[0].strip()
    if "Final Answer:" in response_content:
        final_answer = response_content.split("Final Answer:")[1].strip()
    

    return thought, action, action_input, final_answer

def log_response(thought, action, action_input, final_answer):
    # log the response
    print("\n" + "="*50)
    print("Thought:", thought)
    print("-"*50)
    print("Action:", action)
    print("-"*50)
    print("Action Input:", action_input)
    print("-"*50)
    if final_answer:
        print("Final Answer:", final_answer)
    print("="*50 + "\n")

def generate_text(prompt):
    try:
        for i in range(5):
            context = prompts.CONTEXT_PROMPT.format(
                table_schema=table_schema_str,
                user_query=prompt,
                iteration_history=iteration_history
            )
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": prompts.SYSTEM_PROMPT},
                    {"role": "user", "content": context}
                ]
            )
            
            # Get the current loop's response content from LLM
            response_content = response.choices[0].message.content
            iteration_history.append(response_content)
            
            # Parse the response from LLM
            thought, action, action_input, final_answer = parse_response(response_content)
            print('LOOP:', i)
            log_response(thought, action, action_input, final_answer)
            
            # Execute the action input if it is a SQL query
            if action_input:
                result = execute_sql_query(action_input)
                iteration_history.append(result)
                print("SQL Result:", result)
            
            # if final answer is generated, print it and break the loop
            if final_answer:
                print('-'*100)
                print(f"\033[92m{final_answer}\033[0m")
                break

        return response_content
    except Exception as e:
        print(f"Error generating text: {str(e)}")
        return None

if __name__ == "__main__":
    prompt = "what is the average engagement score for the course? show in a graph"
    result = generate_text(prompt)
