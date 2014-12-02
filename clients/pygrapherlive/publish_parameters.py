# for sftp via pysftp to save and upload the plot
imagePath = '/home/cct/LabRAD/common/clients/pygrapherlive/temp_images'
un = 'haeffneradmin'
pw = '/home/cct/ssh_test/testkey' # this should be the path to the private key
# privwinkey.ppk made by pageant

host = "research.physics.berkeley.edu"
blogPath = 'web/wp-blog/wp-content/uploads/2014/07/'

# for webblog via xmlrpclib to upload the test to the blog
wp_url = "http://research.physics.berkeley.edu/haeffner/wp-blog//xmlrpc.php"
wp_username = "haeffner" # replace with ssh key
wp_password = "S12D52" 
categories = ['cct']
tags = [] 

