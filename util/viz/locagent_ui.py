import streamlit as st
import json
import datetime
import os
import subprocess
import sys
import os


class LocAgentUI:
    def __init__(self):
        current_file_path = os.path.abspath(__file__)
        script_dir = os.path.dirname(current_file_path)
        self.loc_agent_dir = os.path.abspath(f"{script_dir}/../../")


    def add_sidebar(self):
        st.sidebar.title("Repo Settings")
        output_folder = st.sidebar.text_input("Enter output folder", value=None)
        repo = st.sidebar.text_input("Enter github repo: Repo url will be built as https://github.com/{repo}.git")
        commit_id = st.sidebar.text_input("Enter base commit id to checkout")
        download_repo = st.sidebar.checkbox("Download repo")

        if download_repo:
            st.sidebar.info(f"{repo} will be downloaded")
            local_repo_path = None
        else:
            local_repo_path = st.sidebar.text_input("Enter local path to repo", value="")

        model_name = st.sidebar.text_input(f"Enter model name. If hosted. on vllm, enter hosted_vllm/<your modelname>")
        openai_api_key = st.sidebar.text_input(f"Enter OpenAI API key", type="password")
        openai_base_url = st.sidebar.text_input(f"Enter base URL for OpenAI API: ex: http://127.0.0.1:8055/v1")

        if output_folder is not None and not os.path.exists(output_folder):
            os.makedirs(output_folder)
            

        return {
            "output_folder": output_folder,
            "repo": repo,
            "commit_id": commit_id,
            "download_repo": download_repo,
            "local_repo_path": local_repo_path,
            "model_name": model_name,
            "openai_api_key": openai_api_key,
            "openai_base_url": openai_base_url
        }
    

    def execute_python_file(self, file_path, args, env_args=None):
        """
        Execute a Python file using subprocess and return the results
        """
        try:
            env={
                **os.environ,  # Include existing environment variables
                'PYTHONPATH': f"{self.loc_agent_dir}",
            }
            if env_args is not None:
                env.update(**env_args)
            result = subprocess.run(
                [sys.executable, file_path] + args,
                capture_output=True,
                text=True,
                timeout=None,
                env=env
            )
            return {
                'success': result.returncode == 0,
                'output': result.stdout,
                'error': result.stderr,
                'returncode': result.returncode
            }
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'output': '',
                'error': 'Script execution timed out (60 seconds)',
                'returncode': -1
            }
        except Exception as e:
            return {
                'success': False,
                'output': '',
                'error': str(e),
                'returncode': -1
            }

    def _is_same_query(self, query):
        if st.session_state["prev_user_query"] is None:
            return False
        else:
            return st.session_state["prev_user_query"][0]["repo"] == query[0]["repo"]  and \
                   st.session_state["prev_user_query"][0]["problem_statement"].strip() == query[0]["problem_statement"].strip() and \
                   st.session_state["prev_user_query"][0]["base_commit"] == query[0]["base_commit"]
                    

    def create_user_query(self):

        container_user_query = st.container(border=True, key="container_user_query")
        st.session_state.is_same_query = False
        
        def click_query_button():
            repo = self.metadata["repo"]
            _id = datetime.datetime.now().isoformat()
            instance_id = repo.replace("/", "__") + "-" +  _id

            data = [{
                "repo": self.metadata["repo"],
                "instance_id": instance_id,
                "base_commit": self.metadata["commit_id"],
                "problem_statement": user_query
            }]

            is_same_query = self._is_same_query(data)
            st.session_state.is_same_query = is_same_query
            if is_same_query:
                with container_user_query:
                    st.info("This query is similar to a previous query.")
            else:
                with container_user_query:
                    st.info("This query is different from previous queries.")
                user_query_file_path = os.path.join(self.metadata["output_folder"], f"user_queries_{_id}.json")
                st.session_state["prev_user_query"] = data
                st.session_state["prev_user_query_file_path"] = user_query_file_path

                # Save the user query to a JSON file
                with open(user_query_file_path, "w") as f:
                    json.dump(data, f)

        with container_user_query:
            user_query_file_path = None
            user_query = st.text_area("Enter your query:")
            if "prev_user_query" not in st.session_state:
                st.session_state["prev_user_query"] = None

            if "prev_user_query_file_path" not in st.session_state:
                st.session_state["prev_user_query_file_path"] = None

            st.button('Done with user query', on_click=click_query_button)

        return st.session_state["prev_user_query_file_path"]


    def build_graph(self, user_query_file_path):

        container_graph = st.container(border=True, key="container_graph")
        if "build_graph_result" not in st.session_state:
            st.session_state.build_graph_result = None

        def click_graph_button():
            with container_graph:
                if st.session_state.build_graph_result is None:
                    st.write('Building graph for repo')
            # Step 1: Build graph of the repo

            if not self.metadata["download_repo"]:
                repo_path = self.metadata["local_repo_path"]
            else:
                repo_path = os.path.join(self.metadata["output_folder"], "playground/build_graph")

            index_dir_path = os.path.join(self.metadata["output_folder"], "index_data")

            args = ["--dataset", user_query_file_path, 
                "--split", "test",
                "--repo_path", repo_path,
                "--load_from_json",
                "--num_processes", "1",
                "--index_dir", index_dir_path
            ]

            if self.metadata["download_repo"]:
                args += ["--download_repo"]

            # Execute python script `dependency_graph/batch_build_graph.py`
            if st.session_state.build_graph_result is None:
                with container_graph:
                    with st.spinner(f"Executing dependency_graph/batch_build_graph.py with args: {args}", show_time=True):
                        result = self.execute_python_file(os.path.abspath(f"{self.loc_agent_dir}/dependency_graph/batch_build_graph.py"), args)
                st.session_state.build_graph_result = result
        
        def click_reset_graph():
            with container_graph:
                st.info("Graph reset, please click build graph again to execute script before proceeding")
            st.session_state.build_graph_result = None

        with container_graph:
            cols = st.columns(2)
            with cols[0]:
                st.button('Build Graph', on_click=click_graph_button, key="build_graph")
            with cols[1]:
                st.button("Reset graph", on_click=click_reset_graph, key="rebuild_graph")

            with container_graph:
                if st.session_state.build_graph_result is not None:
                    st.write(st.session_state.build_graph_result)
                    if st.session_state.build_graph_result["success"]:
                        st.success("Graph built successfully!")
                    else:
                        st.error("Error building Graph")

    def build_bm25_graph_index(self, user_query_file_path):
        # Step 2: Build BM25 index for the repo

        container_bm25 = st.container(border=True, key="container_bm25")
        if "build_bm25_result" not in st.session_state:
            st.session_state.build_bm25_result = None

        def click_bm25_index_button():
            with container_bm25:
                if st.session_state.build_bm25_result is None:
                    st.write('Building BM25 index for repo')

            if not self.metadata["download_repo"]:
                repo_path = self.metadata["local_repo_path"]
            else:
                repo_path = os.path.join(self.metadata["output_folder"], "playground/build_graph")

            index_dir_path = os.path.join(self.metadata["output_folder"], "index_data")

            args = [
                "--dataset", user_query_file_path,
                "--split", "test",
                "--repo_path", repo_path,
                "--load_from_json",
                "--num_processes", "1",
                "--index_dir", index_dir_path
            ]

            # Execute python script `dependency_graph/batch_build_graph.py`
            if st.session_state.build_bm25_result is None:
                with container_bm25:
                    with st.spinner(f"Executing build_bm25_index.py with args: {args}", show_time=True):
                        result = self.execute_python_file(os.path.abspath(f"{self.loc_agent_dir}/build_bm25_index.py"), args)
                st.session_state.build_bm25_result = result
        
        
        def click_reset_bm25_index():
            with container_bm25:
                st.info("BM25 index reset, please click `Build BM25 Index` again to execute script before proceeding")
            st.session_state.build_bm25_result = None

        with container_bm25:
            cols = st.columns(2)
            with cols[0]:
                st.button('Build BM25 Index', on_click=click_bm25_index_button, key="build_bm25_index")
            with cols[1]:
                st.button("Reset BM25 Index", on_click=click_reset_bm25_index, key="rebuild_bm25_index")

            with container_bm25:
                if st.session_state.build_bm25_result is not None:
                    st.write(st.session_state.build_bm25_result)
                    if st.session_state.build_bm25_result["success"]:
                        st.success("BM25 index built successfully!")
                    else:
                        st.error("Error building BM25 index")

    def launch_loc_agent(self, user_query_file_path):

        container_autosearch = st.container(border=True, key="container_autosearch")
        if "autosearch_result" not in st.session_state:
            st.session_state.autosearch_result = None

        def click_autosearch_button():
            with container_autosearch:
                if st.session_state.autosearch_result is None:
                    st.write('Launching Agent for repo')

            if not self.metadata["download_repo"]:
                repo_path = self.metadata["local_repo_path"]
            else:
                repo_path = os.path.join(self.metadata["output_folder"], "playground/build_graph")
            index_dir_path = os.path.join(self.metadata["output_folder"], "index_data")
            dataset_name = os.path.basename(user_query_file_path)

            args = [
                "--dataset", user_query_file_path, 
                "--split", "test",
                "--model", self.metadata["model_name"],
                "--localize",
                "--merge",
                "--output_folder", os.path.join(self.metadata["output_folder"], "location"),
                "--eval_n_limit", "300",
                "--num_processes", "1",
                "--use_function_calling",
                "--simple_desc",
                "--load_from_json"
            ]

            env_args = {
                "OPENAI_API_KEY": self.metadata["openai_api_key"],
                "OPENAI_API_BASE": self.metadata["openai_base_url"],
                "GRAPH_INDEX_DIR": f"{index_dir_path}/{dataset_name}/graph_index_v2.3",
                "BM25_INDEX_DIR": f"{index_dir_path}/{dataset_name}/BM25_index"
            }

            # Execute python script `dependency_graph/batch_build_graph.py`
            # Run always
            with container_autosearch:
                with st.spinner(f"Executing auto_search_main.py with args: {args}", show_time=True):
                    result = self.execute_python_file(os.path.abspath(f"{self.loc_agent_dir}/auto_search_main.py"), args, env_args)
            st.session_state.autosearch_result = result


        def click_reset_autosearch():
            with container_autosearch:
                st.info("Autosearch reset, please click `Launch Agent` again to execute script before proceeding")
            st.session_state.autosearch_result = None

        with container_autosearch:
            cols = st.columns(2)
            with cols[0]:
                st.button('Launch Agent', on_click=click_autosearch_button, key="launch_autosearch")
            with cols[1]:
                st.button("Reset Autosearch", on_click=click_reset_autosearch, key="reset_autosearch")

            if st.session_state.autosearch_result is not None:
                st.write(st.session_state.autosearch_result)
                if st.session_state.autosearch_result["success"]:
                    st.success("Autosearch ran successfully!")
                    # List all files in the output folder and display them
                    output_location_folder = os.path.join(self.metadata["output_folder"], "location")
                    if output_location_folder and os.path.exists(output_location_folder):
                        st.subheader("Files in Output Folder")
                        files = []
                        for root, dirs, filenames in os.walk(output_location_folder):
                            for filename in filenames:
                                files.append(os.path.relpath(os.path.join(root, filename), output_location_folder))
                        if files:
                            for file in files:
                                with st.expander(f"File: {file}"):
                                    file_path = os.path.join(output_location_folder, file)
                                    try:
                                        with open(file_path, "r") as f:
                                            content = f.read()
                                        if file_path.endswith(".json") or file_path.endswith(".jsonl") :
                                            st.json(content)
                                        else:
                                            st.code(content)
                                    except Exception as e:
                                        st.write(f"Could not read file: {e}")
                        else:
                            st.write("No files found in output folder.")
                    else:
                        st.write("Output folder does not exist.")
                else:
                    st.error("Error launching Autosearch")

            
    def run(self):
        st.title("LocAgent")
        st.set_page_config(
            page_title="LocAgent",
            page_icon="✨",
            layout="wide",  # or "centered"
            initial_sidebar_state="expanded"  # or "auto", "collapsed"
        )
        self.metadata = self.add_sidebar()
        user_query_file_path = self.create_user_query()
        # self.build_graph(user_query_file_path)
        # self.build_bm25_graph_index(user_query_file_path)
        self.launch_loc_agent(user_query_file_path)



if __name__ == "__main__":
    LocAgentUI().run()

