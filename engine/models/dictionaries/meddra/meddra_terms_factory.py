from engine.models.dictionaries.meddra.terms.term_types import TermTypes
from engine.models.dictionaries.meddra.terms.meddra_term import MedDRATerm
from engine.models.dictionaries.meddra.meddra_file_names import MeddraFileNames
from engine.models.dictionaries.dictionary_types import DictionaryTypes
from engine.models.dictionaries.terms_factory_interface import (
    TermsFactoryInterface,
)
from typing import List
from engine.exceptions.custom_exceptions import MissingDataError
from engine.utilities.utils import get_dictionary_path
from uuid import uuid4
import asyncio
from io import BytesIO


class MedDRATermsFactory(TermsFactoryInterface):
    """
    This class is a factory that accepts file name
    and contents and creates a term record for each line.
    """

    def __init__(self, data_service=None):
        self.data_service = data_service

    def chunks(self, lst, n):
        """Yield successive n-sized chunks from lst."""
        for i in range(0, len(lst), n):
            yield lst[i : i + n]

    async def install_terms(
        self,
        dictionary_id: str,
        directory_path: str,
        file_name: str,
        file_contents: bytes,
    ):
        """
        Insert MedDRA dictionary terms into appropriate storage.
        """
        files = {
            MeddraFileNames.PT.value: TermTypes.PT.value,
            MeddraFileNames.HLT.value: TermTypes.HLT.value,
            MeddraFileNames.LLT.value: TermTypes.LLT.value,
            MeddraFileNames.SOC.value: TermTypes.SOC.value,
            MeddraFileNames.HLGT.value: TermTypes.HLGT.value,
        }

        relationship_files = [
            MeddraFileNames.SOC_HLGT.value,
            MeddraFileNames.HLGT_HLT.value,
            MeddraFileNames.HLT_PT.value,
        ]
        data = {}

        required_files = list(files.keys()) + relationship_files
        if not self.data_service.has_all_files(directory_path, required_files):
            raise MissingDataError(message="Necessary meddra files missing")
        # Load data
        for file_name, data_type in files.items():
            file_path = get_dictionary_path(dictionary_id, file_name=file_name)
            data[data_type] = self.read_data(file_path, data_type, dictionary_id)

        # Load relationships
        for file_name in relationship_files:
            data = self.update_relationship_data(dictionary_id, file_name, data)

        hierarchy = [
            TermTypes.SOC.value,
            TermTypes.HLGT.value,
            TermTypes.HLT.value,
            TermTypes.PT.value,
            TermTypes.LLT.value,
        ]
        for i, term_type in enumerate(hierarchy):
            if i == 0:
                continue
            for term in data[term_type].values():
                parent_type = hierarchy[i - 1]
                if term.parent_code:
                    parent: MedDRATerm = data[parent_type][term.parent_code]
                    term.parent_term = parent.term
                    term.code_hierarchy = f"{parent.code_hierarchy}/{term.code}"
                    term.term_hierarchy = f"{parent.term_hierarchy}/{term.term}"

        return data

    async def save_terms(self, terms: List[MedDRATerm]):
        MedDRATerm.bulk_insert_items("type", terms)

    def read_data(self, file_path, data_type: str, dictionary_id: str) -> dict:
        """
        Parse file and generate appropriate MedDRATerms
        """
        parser_map: dict = {
            TermTypes.PT.value: self._parse_pt_item,
            TermTypes.HLT.value: self._parse_hlt_item,
            TermTypes.LLT.value: self._parse_llt_item,
            TermTypes.SOC.value: self._parse_soc_item,
            TermTypes.HLGT.value: self._parse_hlgt_item,
        }
        parser = parser_map[data_type]
        file_data = BytesIO(self.data_service.read_data(file_path))
        data = {}
        for line in file_data:
            line = line.decode("utf-8")
            value = parser(line, dictionary_id)
            data[value.code] = value
        return data

    def update_relationship_data(self, dictionary_id, file_name, data) -> dict:
        """
        Iterates over lines in a relationship file, and sets the
        parent relationship on the appropriate term
        """
        origin_type, target_type = file_name.split("_")
        target_type = target_type.split(".")[0]
        file_path = get_dictionary_path(dictionary_id, file_name=file_name)
        file_data = BytesIO(self.data_service.read_data(file_path))
        for line in file_data:
            line = line.decode("utf-8")
            origin_code, target_code = line.split("$")[:2]
            origin_item: MedDRATerm = data[origin_type][origin_code]
            target_item: MedDRATerm = data[target_type][target_code]
            target_item.set_parent(origin_item)

        return data

    def _parse_pt_item(self, item: str, dictionary_id: str) -> MedDRATerm:
        """
        Parses a row from pt.asc and creates a MedDRATerm
        """
        item = item.strip("$")
        values = item.split("$")
        return MedDRATerm(
            {
                "code": values[0],
                "term": values[1],
                "parentCode": values[3],
                "type": TermTypes.PT.value,
                "id": str(uuid4()),
                "dictionaryType": DictionaryTypes.MEDDRA.value,
                "dictionaryId": dictionary_id,
            }
        )

    def _parse_hlt_item(self, item: str, dictionary_id: str) -> MedDRATerm:
        """
        Parses a row from hlt.asc and creates a MedDRATerm
        """
        item = item.strip("$")
        values = item.split("$")
        return MedDRATerm(
            {
                "code": values[0],
                "term": values[1],
                "type": TermTypes.HLT.value,
                "id": str(uuid4()),
                "dictionaryType": DictionaryTypes.MEDDRA.value,
                "dictionaryId": dictionary_id,
            }
        )

    def _parse_llt_item(self, item: str, dictionary_id: str) -> MedDRATerm:
        """
        Parses a row from llt.asc and creates a MedDRATerm
        """
        item = item.strip("$")
        values = item.split("$")
        return MedDRATerm(
            {
                "code": values[0],
                "term": values[1],
                "type": TermTypes.LLT.value,
                "parentCode": values[2],
                "id": str(uuid4()),
                "dictionaryType": DictionaryTypes.MEDDRA.value,
                "dictionaryId": dictionary_id,
            }
        )

    def _parse_hlgt_item(self, item: str, dictionary_id: str) -> MedDRATerm:
        """
        Parses a row from hlgt.asc and creates a MedDRATerm
        """
        item = item.strip("$")
        values = item.split("$")
        return MedDRATerm(
            {
                "code": values[0],
                "term": values[1],
                "type": TermTypes.HLGT.value,
                "id": str(uuid4()),
                "dictionaryType": DictionaryTypes.MEDDRA.value,
                "dictionaryId": dictionary_id,
            }
        )

    def _parse_soc_item(self, item: str, dictionary_id: str) -> MedDRATerm:
        """
        Parses a row from soc.asc and creates a MedDRATerm
        """
        item = item.strip("$")
        values = item.split("$")
        return MedDRATerm(
            {
                "code": values[0],
                "term": values[1],
                "type": TermTypes.SOC.value,
                "abbreviation": values[2],
                "codeHierarchy": values[0],
                "termHierarchy": values[1],
                "id": str(uuid4()),
                "dictionaryType": DictionaryTypes.MEDDRA.value,
                "dictionaryId": dictionary_id,
            }
        )