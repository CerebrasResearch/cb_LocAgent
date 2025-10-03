from plugins.location_tools.repo_ops.repo_ops import (
    set_current_issue,
    explore_tree_structure,
    explore_tree_structure_for_code_comments
)
from datasets import load_dataset
import os

os.environ["GRAPH_INDEX_DIR"] = "/mlf11-shared/coding/aarti/cb_LocAgent/mz_autosearch_3/index_data/user_queries_2025-08-26T20:29:54.593903.json/graph_index_v2.3"

dataset_path = "/mlf11-shared/coding/aarti/test_modelzoo/user_queries_2025-08-26T20:29:54.593903.json"

bench_data = load_dataset('json', data_files={'test': dataset_path}, split='test')

_tree_args = [
    # {
    #     "start_entities": ["src/cerebras/modelzoo/models"],
    #     "direction": "downstream",
    #     "traversal_depth": -1,
    #     "entity_type_filter": ["directory"],  # 'class', 'function', 'file', 'directory')
    #     "dependency_type_filter": ["imports", "invokes", "inherits", "contains"],  # 'contains', 'imports', 'invokes', 'inherits'
    #     "output_path": "/mlf11-shared/coding/aarti/cb_LocAgent/scripts/logs/get_outputs_directory_downstream.txt"
    # },
    # {
    #     "start_entities": ["src/cerebras/modelzoo/models"],
    #     "direction": "upstream",
    #     "traversal_depth": -1,
    #     "entity_type_filter": ["directory"],  # 'class', 'function', 'file', 'directory')
    #     "dependency_type_filter": ["imports", "invokes", "inherits", "contains"],  # 'contains', 'imports', 'invokes', 'inherits'
    #     "output_path": "/mlf11-shared/coding/aarti/cb_LocAgent/scripts/logs/get_outputs_directory_upstream.txt"
    # },
    # {
    #     "start_entities": ["src/cerebras/modelzoo/models"],
    #     "direction": "downstream",
    #     "traversal_depth": -1,
    #     "entity_type_filter": ["directory", "file"],  # 'class', 'function', 'file', 'directory')
    #     "dependency_type_filter": ["imports", "invokes", "inherits", "contains"],  # 'contains', 'imports', 'invokes', 'inherits'
    #     "output_path": "/mlf11-shared/coding/aarti/cb_LocAgent/scripts/logs/get_outputs_file_downstream.txt"
    # },
    # {
    #     "start_entities": ["src/cerebras/modelzoo/models"],
    #     "direction": "upstream",
    #     "traversal_depth": -1,
    #     "entity_type_filter": ["directory", "file"],  # 'class', 'function', 'file', 'directory')
    #     "dependency_type_filter": ["imports", "invokes", "inherits", "contains"],  # 'contains', 'imports', 'invokes', 'inherits'
    #     "output_path": "/mlf11-shared/coding/aarti/cb_LocAgent/scripts/logs/get_outputs_file_upstream.txt"
    # },
    # {
    #     "start_entities": ["src/cerebras/modelzoo/models/vision/vision_transformer/ViTModel.py"],
    #     "direction": "downstream",
    #     "traversal_depth": -1,
    #     "entity_type_filter": ["directory", "file", "class", "function"],  # 'class', 'function', 'file', 'directory')
    #     "dependency_type_filter": ["imports", "invokes", "inherits", "contains"],  # 'contains', 'imports', 'invokes', 'inherits'
    #     "output_path": "/mlf11-shared/coding/aarti/cb_LocAgent/scripts/logs/get_outputs_ViT.txt"
    # },
    # {
    #     "start_entities": ["src/cerebras/modelzoo/models/vision/vision_transformer/ViTModel.py"],
    #     "direction": "downstream",
    #     "traversal_depth": 2,
    #     "entity_type_filter": ["directory", "file", "class", "function"],  # 'class', 'function', 'file', 'directory')
    #     "dependency_type_filter": ["imports", "invokes", "inherits", "contains"],  # 'contains', 'imports', 'invokes', 'inherits'
    #     "output_path": "/mlf11-shared/coding/aarti/cb_LocAgent/scripts/logs/get_outputs_ViT_depth2.txt"
    # },
    {
        "start_entities": ["src/cerebras/modelzoo/models/vision/vision_transformer/ViTModel.py"],
        "direction": "downstream",
        "traversal_depth": 2,
        "entity_type_filter": ["directory", "file", "class", "function"],  # 'class', 'function', 'file', 'directory')
        "dependency_type_filter": ["contains"],  # 'contains', 'imports', 'invokes', 'inherits'
        "output_path": "/mlf11-shared/coding/aarti/cb_LocAgent/scripts/logs/get_outputs_ViT_depth2_contains_noempty.txt"
    },
]

for bug in bench_data:
    instance_id = bug["instance_id"]
    set_current_issue(instance_data=bug, rank=0)

    for val in _tree_args:
        output_path = val.pop("output_path")
        # output = explore_tree_structure(**val)
        output = explore_tree_structure_for_code_comments(**val)

        with open(output_path, "w") as f:
            f.write(f"Args: {str(val)}")
            f.write("\n\n")
            f.write("=============================\n\n")
            f.write(str(output[0]))
            f.write("\n\n")
            f.write("=============================\n\n")
            f.write(str(output[1]))


        

