#from api.services.langchain.chatbot import test_chatbot


from api.tests.test_db_setup import test_db_setup
from api.services.sop_service.tests import run_sop_service_test

test_db_setup()
run_sop_service_test()