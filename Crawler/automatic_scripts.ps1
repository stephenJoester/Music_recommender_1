# Set the path to the notebook and output notebook
$notebook_path = "D:\NgHoangQuan\Code_test\PBL7\Crawler\spotify_crawler.ipynb"
$output_path = "D:\NgHoangQuan\Code_test\PBL7\Crawler\spotify_crawler_output.ipynb"

# Change directory to the desired location
Set-Location "D:\NgHoangQuan\Code_test\PBL7\Crawler"

# Run papermill command
papermill $notebook_path $output_path
