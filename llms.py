from prompts import *
from typing import List

from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from pydantic import BaseModel, Field
from langchain_groq import ChatGroq
model = ChatGroq(
    model="llama-3.1-70b-versatile",
    temperature=0,)

# Define your desired data structure.
class claimClass(BaseModel):
    category: str = Field(description="municipal committee domain chosen for the claim")

class claimKeywords(BaseModel):
    topics: List = Field(description="List of Keywords/topics for municipal claims.")

def analyze_text(claim):
    category = predict_class(claim)
    keywords = predict_keywords(claim)
    return category, keywords

def predict_class(claim):
    # Set up a parser + inject instructions into the prompt template.
    parser = JsonOutputParser(pydantic_object=claimClass)

    prompt = PromptTemplate(
        template=category_prompt,
        input_variables=["claim", "municipality"],
        partial_variables={"format_instructions": parser.get_format_instructions()},
    )

    chain = prompt | model | parser
    response = chain.invoke({"claim": claim['claim'], "municipality": claim['municipality']})['category']

    return response

# Define your desired data structure.
def predict_keywords(claim):
    # Set up a parser + inject instructions into the prompt template.
    parser = JsonOutputParser(pydantic_object=claimKeywords)

    prompt = PromptTemplate(
        template=keywords_prompt,
        input_variables=["claim", "municipality"],
        partial_variables={"format_instructions": parser.get_format_instructions()},
    )

    chain = prompt | model | parser
    response = chain.invoke({"claim": claim['claim'], "municipality": claim['municipality']})['topics']

    return response
