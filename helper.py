import psycopg2
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.tools import tool
from langchain_core.messages import HumanMessage, ToolMessage
from langchain_core.output_parsers import JsonOutputParser
import logging
import json
import re
import os
from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DBoperation:
    def __init__(self):
        self.connection = psycopg2.connect(
            dbname=os.getenv("DBNAME"),
            user=os.getenv("USER"),
            password=os.getenv("PASSWORD"),
            host=os.getenv("HOST"),
            port=os.getenv("PORT")
        )
        self.cursor = self.connection.cursor()
        
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            temperature=0.2,
            api_key=os.getenv("GOOGLE_API_KEY"),
        )

    def _get_all_ac_data(self):
        """Internal method to fetch all air conditioner products from the database."""
        try:
            self.cursor.execute("SELECT * FROM ac")
            res = self.cursor.fetchall()
            if not res:
                return {"error": "No data found in the database."}
            resar = []
            for item in res:
                resdict = {
                    "id": item[0],
                    "name": item[1],
                    "desc": item[2],
                    "image": item[3],
                    "price": item[4]
                }
                resar.append(resdict)
            return {"msg": "success", "data": resar}
        except Exception as e:
            logger.error(f"Error in get_all_ac_data: {str(e)}")
            return {"error": f"Database error: {str(e)}"}

    def _get_all_tv_data(self):
        """Internal method to fetch all TV products from the database."""
        try:
            self.cursor.execute("SELECT * FROM tv")
            res = self.cursor.fetchall()
            if not res:
                return {"error": "No data found in the database."}
            resar = []
            for item in res:
                resdict = {
                    "id": item[0],
                    "name": item[1],
                    "desc": item[2],
                    "image": item[3],
                    "price": item[4]
                }
                resar.append(resdict)
            return {"msg": "success", "data": resar}
        except Exception as e:
            logger.error(f"Error in get_all_tv_data: {str(e)}")
            return {"error": f"Database error: {str(e)}"}

    def _get_all_phones_data(self):
        """Internal method to fetch all phone products from the database."""
        try:
            self.cursor.execute("SELECT * FROM phone")
            res = self.cursor.fetchall()
            if not res:
                return {"error": "No data found in the database."}
            resar = []
            for item in res:
                resdict = {
                    "id": item[0],
                    "name": item[1],
                    "desc": item[2],
                    "image": item[3],
                    "price": item[4]
                }
                resar.append(resdict)
            return {"msg": "success", "data": resar}
        except Exception as e:
            logger.error(f"Error in get_all_phones_data: {str(e)}")
            return {"error": f"Database error: {str(e)}"}
    
    
    def _get_particular_phone(self,brand):
        brand= brand.lower()
        self.cursor.execute("SELECT * FROM phone WHERE category = %s", (brand,))
        res = self.cursor.fetchall()
        if not res:
            return {"error": "No data found in the database."}
        resar = []
        for item in res:
            redict={}
            redict["id"] = item[0]
            redict["name"] = item[1]
            redict["desc"] = item[2]
            redict["image"] = item[3]
            redict["price"] = item[4]
            resar.append(redict)
        return {"msg": "success", "data": resar}
    
    def _get_particular_model(self, model_name,brand):
        model_name = model_name.lower()
        brand  = brand.lower()
        """Internal method to fetch a specific model from the database."""
        try:
            self.cursor.execute("SELECT * FROM phone WHERE category=%s and name = %s", (brand,model_name,))
            res = self.cursor.fetchall()
            if not res:
                return {"error": "No data found for the specified model."}
            resar = []
            for item in res:
                resdict = {
                    "id": item[0],
                    "name": item[1],
                    "desc": item[2],
                    "image": item[3],
                    "price": item[4]
                }
                resar.append(resdict)
            return {"msg": "success", "data": resar}
        except Exception as e:
            logger.error(f"Error in get_particular_model: {str(e)}")
            return {"error": f"Database error: {str(e)}"}
    
    def parse_llm_response(self, response_content):
        """Parse the LLM response to extract the tool call."""
        try:
            # Remove markdown code block if present
            content = response_content
            if "```json" in content:
                content = re.search(r"```json\n(.*?)\n```", content, re.DOTALL)
                if content:
                    content = content.group(1)
            
            # Parse the JSON
            tool_call = json.loads(content)
            return tool_call
        except Exception as e:
            logger.error(f"Error parsing LLM response: {str(e)}")
            return None

    def call_llm_tool_function_call(self, us_query: str):
        """Process user query and call the appropriate tool using Gemini."""
        logger.info(f"Processing user query: {us_query}")
        try:
            # Create tool functions that have access to self
            @tool
            def get_all_ac_data():
                """Fetch all air conditioner products from the database."""
                return self._get_all_ac_data()
            
            @tool
            def get_all_tv_data():
                """Fetch all TV products from the database."""
                return self._get_all_tv_data()
            
            @tool
            def get_all_phones_data():
                """Fetch all phone products from the database."""
                return self._get_all_phones_data()
            
            @tool
            def get_particular_phone(brand: str):
                """Fetch phones of a specific brand (e.g., 'samsung', 'iphone')."""
                return self._get_particular_phone(brand)
            
            @tool
            def get_particular_model(model_name: str, brand: str):
                """Fetch a specific phone model from a brand (e.g., 'samsung galaxy s23', 'samsung')."""
                return self._get_particular_model(model_name, brand)
            # Define available tools
            tools = [get_all_ac_data, get_all_tv_data, get_all_phones_data,get_particular_phone,get_particular_model]
            
            # Bind tools to the LLM
            llm_with_tools = self.llm.bind_tools(tools)
            
            print("2")
            # Create the prompt
            prompt = f"""
            You are an assistant for an e-commerce platform.
            
            You must respond to the user's query in one of two ways:

            1. **Tool Call** – If the query is about products, use one of these tools:
            - Air Conditioners → use `"get_all_ac_data"`
            - Televisions → use `"get_all_tv_data"`
            - All Mobile Phones → use `"get_all_phones_data"`
            - Specific Brand Phones (e.g., "show me all iphones" or "show samsung phones" or "simply the brand name is given") → use `"get_particular_phone"` with brand parameter
            - Specific Phone Model (e.g., "show me samsung galaxy s23" or "i want" or "do you have" or "simply the model name is given") → use `"get_particular_model"` with model_name and brand parameters

            Respond in this format (and **only if applicable**):
            {{
            "name": "tool_name",
            "args": {{
                // Include parameters only for get_particular_phone and get_particular_model
                // For get_particular_phone: "brand": "brand_name"
                // For get_particular_model: "model_name": "model_name", "brand": "brand_name"
            }}
            }}

            2. **Normal Message** – If the query is not asking about products or is a greeting, question, or anything unrelated (e.g., "hello", "how are you", "home"), just respond with a natural message **instead of a tool call**.

            **Do not attempt a tool call** if the user's query is not clearly about one of the product types above.

            ---

            User query: "{us_query}"
            """

            
            print("3")
            # Send the query to the LLM
            messages = [HumanMessage(content=prompt)]
            response = llm_with_tools.invoke(messages)
            
            print("4")
            # Debug: Print the raw response
            print("LLM Response:", response)
            
            # Parse the response content
            if hasattr(response, 'content'):
                tool_call = self.parse_llm_response(response.content)
                if tool_call and 'name' in tool_call:
                    tool_name = tool_call['name']
                    
                    # Map tool names to their corresponding methods
                    tool_map = {
                        'get_all_ac_data': get_all_ac_data,
                        'get_all_tv_data': get_all_tv_data,
                        'get_all_phones_data': get_all_phones_data,
                        'get_particular_phone': get_particular_phone,
                        'get_particular_model': get_particular_model
                    }
                    
                    # Get the appropriate tool
                    selected_tool = tool_map.get(tool_name)
                    if not selected_tool:
                        logger.error(f"Tool {tool_name} not found")
                        return {"error": f"Tool {tool_name} not found."}
                    
                    # Call the tool with the correct invoke method
                    try:
                        # @tool decorated functions need to be called with invoke() and args dict
                        args = tool_call.get('args', {})
                        result = selected_tool.invoke(args)
                        logger.info(f"Tool {tool_name} executed successfully")
                        return result
                    except Exception as e:
                        logger.error(f"Error executing tool {tool_name}: {str(e)}")
                        return {"error": str(e)}
            
            logger.error("No valid tool call generated by the LLM")
            # Debug: Print the response content
            print("Response content:", response.content if hasattr(response, 'content') else "No content")
            return {"tool": response.content}
                
        except Exception as e:
            logger.error(f"Error in call_llm_tool_function_call: {str(e)}")
            return {"tool": response.content}

    # Keep these methods for direct API calls
    def get_all_ac_data(self):
        """Public method for direct API calls."""
        return self._get_all_ac_data()
    
    def get_all_tv_data(self):
        """Public method for direct API calls."""
        return self._get_all_tv_data()
    
    def get_all_phones_data(self):
        """Public method for direct API calls."""
        return self._get_all_phones_data()

    def close(self):
        self.cursor.close()
        self.connection.close()


# if __name__ == "__main__":
#     db_op = DBoperation()
    # try:
        # Example usage
        
        # print(db_op.get_particular_phone("samsung"))
        # print(db_op._get_particular_model("samsung galaxy s23","samsung"))
    
        
    # finally:
    #     db_op.close()