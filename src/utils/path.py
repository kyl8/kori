import glob
import os

def choose_csv_file(interactive=True):
	"""search for all CSV files in src/ and optionally let the user select one. 
	if interactive is False, return the first match or none.
	"""
	src_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
	csv_files = glob.glob(os.path.join(src_dir, '**', '*.csv'), recursive=True)
	if not csv_files:
		print("No CSV files found.")
		return None
	if not interactive:
		for f in csv_files:
			if f.endswith(os.path.join('constants', 'dataset.csv')):
				return f
		return csv_files[0]

	print("Available CSV files:")
	for idx, file in enumerate(csv_files, 1):
		print(f"{idx}: {file}")
	while True:
		try:
			choice = int(input(f"Select a CSV file [1-{len(csv_files)}]: "))
			if 1 <= choice <= len(csv_files):
				return csv_files[choice - 1]
		except ValueError:
			pass
		print("Invalid selection. Please try again.")


def get_dataset_csv_path(fallback_to_search=True, interactive=False):
	"""return the absolute path to constants/dataset.csv
	if that path doesn't exist and fallback_to_search is True, try to find a CSV
	with choose_csv_file() and return it. 
	"""
	base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
	dataset_path = os.path.join(base_dir, 'constants', 'dataset.csv')
	if os.path.exists(dataset_path):
		return dataset_path
	if fallback_to_search:
		found = choose_csv_file(interactive=interactive)
		if found:
			return found
	raise FileNotFoundError(f"dataset.csv not found at {dataset_path} and no other CSV found")
