from fastapi import FastAPI, Depends
from src.utils.user import get_current_user
from src.urls import register_routers
from src.utils.exeptions import CustomApiException, custom_api_exception_handler


app = FastAPI(title="Twitter", debug=True, dependencies=[Depends(get_current_user)])

register_routers(app)

app.add_exception_handler(CustomApiException, custom_api_exception_handler)
