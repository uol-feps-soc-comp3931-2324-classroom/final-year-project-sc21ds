import pandas as pd
from langchain_mistralai.chat_models import ChatMistralAI
from sql_rag import DeepSeek
from langchain_mistralai.chat_models import ChatMistralAI
from langchain.chains import LLMChain
from langchain_community.utilities import SQLDatabase
from langchain_experimental.sql import SQLDatabaseChain

from mysql.connector import errors
from langchain_core._api.deprecation import LangChainDeprecationWarning
from langchain.memory import ConversationBufferMemory


from langchain.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
from langchain_community.chat_models import ChatOllama

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from langchain.output_parsers.openai_functions import JsonOutputFunctionsParser

import json

import pprint
# Read the CSV file into a DataFrame
filepath = 'articles_data.csv'
df = pd.read_csv(filepath)

# Get the column names
columns = df.columns

# Print the column names
#print(df['Title'][0])

def ExtractDataRow(index):
    return df['Title'][index] , df['Article Content'][index] 
    deepseek_model = 'deepseek-coder:6.7b-instruct-q4_0'
    deepseek = DeepSeek(model_name=deepseek_model)()

    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
    prompt_rough = ChatPromptTemplate(
        messages=[
                SystemMessagePromptTemplate.from_template(
                    """
                        **Role:**
                        -Using the Article Title and content generate a list of Question and Answers for the given article in JSON format.

                        **Output**
                        You will only output the JSON format of the Question and Answers for the given article.
                        
                        """

                        
                ),
                MessagesPlaceholder(variable_name="chat_history"),
                HumanMessagePromptTemplate.from_template("{question}")
            ]
        )
    conversation = LLMChain(
            llm=deepseek,
            prompt=prompt_rough,
            verbose=False,
            memory=memory
        )

    conversation({"question": question})
    cleaned_query_result = memory.buffer[-1].content.replace('\\', '')

    return cleaned_query_result

def RunLLM(article_content):

    prompt = ChatPromptTemplate.from_template("""
        **Role:**
        -Using the Article Title and content generate a list of 4 Question and Answers.

        **Output**
        Only output in JSON format with key Questions.                                                                                
        
        article: {foo}""")
    model = ChatOpenAI(openai_api_key="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", model_name="gpt-3.5-turbo",response_format={ "type": "json_object" })
    chain = prompt | model 

    Res = chain.invoke({"foo": article_content})


    # Remove 'json' from the string if LLm response contains it
    if 'json' in Res.content:
        Res.content = Res.content.replace('json', '')
    
    return Res.content

def CombineJsonFile(Index,Title, ArticleInfo, QuestionAnswerList):

    Data = {
        "Index": Index,
        "Title": Title,
        "ArticleContent": ArticleInfo,
        "Q&As": QuestionAnswerList['Questions']
    }

    return Data

def MainFunction():
    # Read existing JSON data from file
    try:
        with open('data.json', 'r') as file:
            existing_data = json.load(file)
    except FileNotFoundError:
        # If the file doesn't exist, initialize with an empty list
        existing_data = []

    # print(len(df))

    for i in range(0, len(df)):

        # Check if the index already exists
        index_exists = any(entry.get("Index") == i for entry in existing_data)

        # Append new data to existing data only if the index doesn't already exist
        if not index_exists:
        # if 1 == 1 :
            Title, ArticleInfo = ExtractDataRow(i)
            content = "Title: " + Title + ", Article Content: " + ArticleInfo

            Response = RunLLM(content)

            # print(Response)

            Response = json.loads(Response)

            # print(Response)

            pprint.pprint(Response, indent=4)

            Result = CombineJsonFile(i, Title, ArticleInfo, Response)

            print(type(Result))

            existing_data.append(Result)
            print("Data appended successfully Index:", i)

        else:
            print("Index already exists in the data.")

        # Dump the updated data into the file after every 10 iterations
        if i % 5 == 0:
            with open('data.json', 'w') as file:
                json.dump(existing_data, file, indent=4)
                print("Data dumped into data.json file.")

    # Write the final updated data back to the file
    with open('data.json', 'w') as file:
        json.dump(existing_data, file, indent=4)
        print("Final data dumped into data.json file.")



MainFunction()