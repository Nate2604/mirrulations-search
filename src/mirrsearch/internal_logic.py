from mirrsearch.db import get_db


class InternalLogic:  # pylint: disable=too-few-public-methods
    def __init__(self, database, db_layer=None):
        self.database = database
        self.db_layer = db_layer

    def search(self, query, document_type_param=None, agency=None, cfr_part_param=None):
        db_layer = self.db_layer if self.db_layer is not None else get_db()
        search_results = db_layer.search(query, document_type_param, agency, cfr_part_param)

        search_results = [
            {
                "docket_id": "Test_Id",
                "title": "Test Title",
                "cfrPart": "Test CFR Part",
                "agency_id": "Test Agency ID",
                "docket_type": "Test Docket Type",
                "modify_date": "2026-03-01"

            }
        ]
        return search_results
