from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
 
def create_prompt():
    return ChatPromptTemplate.from_messages([
        ("system", "You are a helpful assistant that answers queries of user."),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}")
    ])