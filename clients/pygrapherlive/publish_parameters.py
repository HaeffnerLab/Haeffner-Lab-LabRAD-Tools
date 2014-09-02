# for sftp via pysftp to save and upload the plot
imagePath = 'C:\Users\Admin\Documents\GitHub\Haeffner-Lab-LabRAD-Tools\clients\pygrapherlive\images\\'
file = open('C:\Users\Admin\Documents\GitHub\Haeffner-Lab-LabRAD-Tools\clients\pygrapherlive\login.txt','r') # replace with ssh key
string = file.read() # replace with ssh key
import ast # replace with ssh key
dict = ast.literal_eval(string) # replace with ssh key
#un = dict['username'] # replace with ssh key
#pw = dict['password'] # replace with ssh key

un = 'ha*'
pw = 'C:\Users\Admin\\testkey' # this should be the path to the private key
# privwinkey.ppk made by pageant

host = "research.physics.berkeley.edu"
blogPath = 'web/wp-blog/wp-content/uploads/2014/07/'

# for webblog via xmlrpclib to upload the test to the blog
wp_url = "http://research.physics.berkeley.edu/haeffner/wp-blog//xmlrpc.php"
wp_username = "h**" # replace with ssh key
wp_password = "***" # replace with ssh key
#wp_password = 'path to other private key'
categories = ['sqip']
tags = [] 
