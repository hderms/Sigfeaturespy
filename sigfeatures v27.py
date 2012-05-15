#TODO: Must add recursive directory creation to create folders which are a mix of the sanitized, user-inputted filename that is being analyzed and the date
#will package the directory tree into a zip-file when a zip-function is called


#imports go here
import os
import csv,select,sys,math
import re
from scipy.cluster.vq import whiten,kmeans,vq
from numpy import array
from statlib import stats
from matplotlib.pyplot import boxplot
from pylab import *
from matplotlib.mlab import PCA
class errorReporter:
    #simple error handler
    #this class defines an interface for errors. If we are using non-interactive mode, will need to subclass this and replae all the methods with non-interactive versions.
    def keyError(self):
        print "No function in this program is allowed to use more than 20 keywords"
    def argError(self):
        print "You used incorrect arguments"
    def fileOpenError(self):
        print "Couldn't open file"
    def typeError(self):
        print "Incorrect type"
    def karg_error(self):
        print "Incorrect keyword arguments: all required must be set."
global errorReporter_inst
errorReporter_inst = errorReporter()

class runtimeAttribute:
    def __init__(self, type=None, value = None, name = None):
        self.type = type
        self.value = value
        self.name = name
    def setter(self, value):
        if self.type == "float":
            self.value = float(value.split()[0])
        if self.type == "int":
            try:
                self.value = int(value.split()[0])
            except:
                errorReporter_inst.typeError()
            
        if self.type == "string":
            
            self.value = str(value)
        
        
class commandCenter:
    #any function in this commandCenter class must be fed arguments with the CLI arguments provided by the user as element 0 in the list. 
    #functions check if they have all the required keywords arguments filled. If this is true, then it follows a branch that is non-interactive, returning when it has reached the end. 
    #otherwise, it will check to see if the program was run in interactive mode. If it is, then it will continue on and do the rest of the code in the function, allowing the interactive mode to supply the necessary information and do its own error handling. 
    # if it is not, then it throws an error and ends prematurely. This means that other interfaces must make sure they have enough information.
    
    def __init__(self):
        #contains all possible commands
        self.d_commands = {'load':self.load,'savet_test':self.save, 'run':self.run,'print_membership':self.print_membership, 't_test':self.t_test,'display':self.display, 'help':self.help, 'kmeans':self.run_kmeans,'set':self.setter,'box_plot':self.box_plot,'pca':self.run_pca}
        self.dataSet_inst = dataSet()
        #initialized as None value so we can check if it is modified in self.run()
        self.csv_fileopen = None
        self.t_test_performed = False
        self.extractable_columns = []

        #the following variable will be a dictionary of function names that point to lists of required arguments. 
        self.required_arguments = {'load':["filename"], 'run_kmeans':['eigenvectors']}
        #testing for this will tell us whether it is appropriate to print to stdout
        self.interactivemode = True
        #will later load in help_dict from a file
        self.help_dict = {'load':'\nload [filename]\nif no arguments are supplied than load goes into interactive mode\n'}

        #dictionary contains a lookup from user inputted variable names to runtimeAttributes so that user can change behavior of the program during runtime. These are effectively global variables.
        self.setattributes = {'path':runtimeAttribute(type="string",value="", name = "path"),
                                    'dummy':runtimeAttribute(type="float", value="", name ="dummy")
                                    }
        self.row_array = []
    def help(self, *largs, **kargs):
        #fucntion should return help info, under-used at this point
        if self.interactivemode:
            if largs[0]:
                if str(largs[0]) in str(self.help_dict):
                    print self.help_dict[largs[0][0]]
                else:
                    print 'no help found for %s' % largs[0][0]
                    
    def command(self,*largs, **kargs):
        #pass command arguments like such "function --variable=value" 
        #so long as function is in self.d_commands. variable,value key pairs will be passed to teh function, it is up to the function to determine what to do with it.
        if len(largs) > 1:
            errorReport_inst.argError()
        command_string = largs[0]
        cmd_dict = {}
        #strip out these control chars
        
        command_string= command_string.replace("\n","").replace("\r","");

        #helper function that calls other functions
        if "#" in command_string:
            command_string = re.sub(r"#.+$","",command_string)
        print command_string

        if command_string.split():
            #only take the first argument as the command
            command_root = command_string.split()[0]

            #~ print command_root
            #slice only the arguments
            list_args = command_string.split()[1:]
            key_args =  re.findall(r"--([\w]+)=([^ ^=]+)",command_string)


            for x in key_args:
                cmd_dict[x[0]] = x[1]
            #~ for x in cmd_dict.items():
                #~ print x
            #~ print command_args
            #check the argument list and generate a dictionary out ofi t
            #check for it in the command keys
            #~ re_groups = re.findall("-[\S
            if command_root in self.d_commands.keys():
                self.d_commands[command_root](largs=list_args, kargs = cmd_dict)
            else:

                print "Command not found\n"
            
            
    def load(self, largs=[], kargs={}):
    #module-ready
        
        print largs
        if len(largs) == 1 or kargs.keys():
            if largs[0] or kargs.keys():
                #we have some arguments in the form of a list
                if not kargs.keys():
                    if len(kargs.keys()) > 20:
                        errorReporter_inst.keyError()
                    print "please don't use keyword arguments with this command"
                    for arb_keyword in kargs.items():
                        key,val = arb_keyword
                        print key,val
                else:
                   
                    #this is the correct thread.
                    #the command arguments are passed as a list
                    if kargs['filename']:
                        #the behavior uses keywords first
                        self.s_filename = kargs['filename']
                    try:
                        self.f_fileopen = open(self.s_filename, 'rb')

                    except:
                        errorReporter_inst.fileOpenError()
                        print "Error"
                    else:
                        self.csv_fileopen = csv.reader(self.f_fileopen)
                     
        if self.interactivemode:
            print 'Loading procedure initiated:\n'
            print 'Name of file?'
            while True:
                self.s_filename = raw_input("$")
                try:
                    self.f_fileopen = open(self.s_filename, 'rb')
                except:
                    print 'file not found'
                else:
                     self.csv_fileopen = csv.reader(self.f_fileopen)
                     break
        columncountlist = []
        mincolumncount = 0
        i = 0

        try:


            print os.path.join(os.getcwd(),self.s_filename+'dir')
            os.mkdir(os.path.join(os.getcwd(),self.s_filename+'dir'))
            os.chdir(os.path.join(os.getcwd(),self.s_filename+'dir'))
        except:
            print "Can't make directory. \n Trying to change to directory."
            try:
                os.chdir(os.path.join(os.getcwd(),self.s_filename+'dir'))
            except:
                print "Can't create directory or change to it"
        else:
            pass
        self.rootdir = os.path.join(os.getcwd())
        if not self.csv_fileopen:
            exit()
        for row in self.csv_fileopen:
            print row
            #make a list of row lengths so we can find the minimum
            self.dataSet_inst.group_column.append(row[1])
            self.dataSet_inst.columncount = len(row)
            columncountlist.append(len(row))

            #add a reference from rownumber to row so we can step through columns easier
            self.dataSet_inst.rowdict[i] = row
            i +=1
        self.dataSet_inst.rowcount = i
        self.dataSet_inst.group_column.pop(0)
        self.dataSet_inst.columncount = min(columncountlist)
        print 'rowcount and column'
        print self.dataSet_inst.rowcount
        print self.dataSet_inst.columncount

    def setter(self, largs=[], **kargs):
        #sets values for runtime variables that are modifiable by the user. This is intended for global variables.
        if not largs:
            if self.interactivemode:
                for pair in self.setattributes.items():
                    if pair[1].value:
                        print "%s value is %s" % (pair[0], pair[1].value)
                    else:
                        print "%s value is %s" % (pair[0], "None")
            
            return
        localargs = largs
        
        if localargs[0] in self.setattributes.keys():
            if len(localargs) == 1:
                if self.interactivemode:
                    print self.setattributes[localargs[0]].value
                
            if len(localargs) > 1:
                
                self.setattributes[localargs[0]].setter(' '.join(localargs[1:]))
                
            
        
    def save(self, largs=[], kargs = {}):
        #only works to save the base data throughout modifications.
        if self.interactivemode:
            print 'Saving procedure initiated:\n'
            if self.t_test_performed:
                print "you have performed a T-test. We will be saving the significant features from the results of that T-test"
            else:
                print "No T-test performed. Returning to main loop"
                return None
            print "Which groups to save?"
            print "input them like so:"
            print "x y"
            print "If you just press enter then you get the default (what you just ran the T-test on"
            #TODO make this regexp actually work lol
            s_save_groups = raw_input("$")
            re_match1 = re.findall(r" *([\w-]{1,9})",s_save_groups)
            if not re_match1:
                print "You did not input groups that you wanted saved. Using default"
                re_match1 = [self.group1.group, self.group2.group]
                print re_match1
        if self.interactivemode:
            print "saving only the left-most (name and group) columns as well as the following:"
            print self.extractable_columns
            print "input filename to save under"
            file_save_name =raw_input("$")
        else:
            file_save_name=os.path.join(self.rootdir,"sigfeatures.csv")
            if set(["group1","group2"]).issubset(kargs.keys()):
                pass
            else:
                re_match1 = [self.group1.group, self.group2.group]
        
        file_save_handler = open(file_save_name,'wb')
        file_csv = csv.writer(file_save_handler)


        
        for row in self.dataSet_inst.rowdict.keys():
            temp_list = []
            #if the current row's group element is either group1 or group2
            print self.dataSet_inst.rowdict[row][1]
            self.extractable_columns = list(set(self.extractable_columns))
            if self.dataSet_inst.rowdict[row][1] in re_match1 or (row == 0):
                #start constructing the list based on what is known to be required (name column and group column)
                temp_list.append(self.dataSet_inst.rowdict[row][0])
                temp_list.append(self.dataSet_inst.rowdict[row][1])
                #construct list further with any optional columns
                for sigfeat in self.extractable_columns:
                    #print self.dataSet_inst.rowdict[row][sigfeat]
                    
                    temp_list.append( self.dataSet_inst.rowdict[row][sigfeat])
            #if a list has been constructed then print it and save it
            if temp_list:
                print temp_list
                file_csv.writerow(temp_list)
            
            
    def display(self, *largs, **kargs):
        #operates simiolar to save() but only displays the rows
        for row in self.dataSet_inst.rowdict.keys():
            temp_list = []
            for x in self.dataSet_inst.rowdict[row]:
                if len(x) < wrap:
                    #padd the string with enouhg multiples to make len(x) = wrap
                    x = str(x)
                    x = x + ( ' '* abs(len(x) - wrap))
                    temp_list.append(x)
                else:
                    temp_list.append(str(x)[:wrap])
            print("   ".join(self.dataSet_inst.rowdict[row]))
    def box_plot(self, largs=[], kargs={}):
        
        print kargs.keys()
        if self.interactivemode:
            print "which groups to generate box plots for?"
            print ' '.join(self.dataSet_inst.groupdict.keys())
            groupsToPlot = raw_input("$")
            print "what should the y-axis be labelled?"
            yaxislab = raw_input("$")
            print "what should be appended to the column name for the title of the graph?"
            title_append = raw_input("$")
            re_match1 = re.findall(r" *([\w-]{1,9})",groupsToPlot)
            print re_match1
        else:
            re_match1 = [kargs[x] for x in kargs.keys() if 'group' in x]
                
            #replace these checks with the default_dict idea
            if 'ylabel' in kargs.keys():
                yaxislab = str(kargs['ylabel'])
            else:
                yaxislab = 'Value'
            if 'title' in kargs.keys():
                title_append = str(kargs['title'])
            else:
                title_append = ''
            print re_match1
        subset =[self.dataSet_inst.groupdict[x] for x in re_match1]
        #a list of the maximum keys (column index) for each group defined
        subset_columncount_list = [max((x.columndict.keys())) for x in subset]
        #list the minimum keys for each group defined
        subset_columncountmin_list = [min((x.columndict.keys())) for x in subset]
        print subset_columncount_list
        #go from the highest low-value to the lowest high-value
        print max(subset_columncountmin_list),min(subset_columncount_list)
        #the plus 2 factor in the end of the range results from not counting the first two columns of the CSV because they are name and group column
        try:
            os.mkdir(os.path.join(self.rootdir,'box_plots'))
            os.mkdir(os.path.join(self.rootdir,'box_plots'))
        except:
            os.chdir(os.path.join(self.rootdir,'box_plots'))
        
        for x in range(max(subset_columncountmin_list),(min(subset_columncount_list)+1)):
            print x,self.dataSet_inst.rowdict[0][x]
            figure_name = (self.s_filename+'_'+self.dataSet_inst.rowdict[0][x]+'.png')
            columnname = self.dataSet_inst.rowdict[0][x]
            boxplotData = [group.columndict[x] for group in subset]
            boxplotTitles = [x.group for x in subset]
            fig=figure()
            ax1=fig.add_subplot(111)
            ax1.set_xlabel('Group')
            ax1.set_ylabel(yaxislab)
            ax1.set_title(columnname + title_append)
            setp(ax1,xticklabels=boxplotTitles)

            ax1.boxplot(boxplotData)
            fig.savefig(figure_name, format='png')
            clf()
            close()
        #~ self.dataSet_inst.groupdict[]
        os.chdir(self.rootdir)
        print os.getcwd()

    def run(self,*largs, **kargs):

        #self.dataSet_inst.calculate_averages()
        self.dataSet_inst.find_groups()
        
    def report(self, *largs, **kargs):
        #easy way to return a list of the commands I've set up in d_commands
        return [x for x in self.d_commands.keys()]
            
            

    def print_membership(self, *largs, **kargs):
        #prints all the groups and then their elements
        for x in self.dataSet_inst.groupdict.keys():

            print "The key is %s" % x
            print self.dataSet_inst.groupdict[x].group
            self.dataSet_inst.groupdict[x].report_membership()
    def t_test(self, *largs, **kargs):
        #uses unequal variance, unpaired student's t-test

        print "Running print_membership so that the user is informed as to which group is assigned to which number"
        self.print_membership()
        print "T-test P-value threshold?"
        self.pvalcriteria= raw_input("$")
        print "Which groups would you like to run the T-test on. We are capped at 2 groups because of the nature of the T-test"
        print "You should format the input as such: x y"
        print "In other words, groups should be separated by a single space"
        s_test_groups = raw_input("$")
        print "do you want to pool t-test results so that you append significant columns without wiping it after each run?"
        pool_flag = raw_input("$")
        #re_match=re.search(r"^([A-Z|a-z|0-9|-|_]{1,9}) ([a-z|A-Z|0-9]{1,9})", s_test_groups)
        re_match = re.search("^([\w-]{1,9}) ([\w-]{1,9})",s_test_groups)
        if re_match:
            if 'no' in pool_flag:
                self.extractable_columns = []
            re_match_list = re_match.groups()
            #these translate the two groups that were specified by the user into the actual statGroup objects
            if (re_match_list[0] in self.dataSet_inst.groupdict.keys()) and (re_match_list[1] in self.dataSet_inst.groupdict.keys()):
                group1 = self.dataSet_inst.groupdict[re_match_list[0]]
                group2 = self.dataSet_inst.groupdict[re_match_list[1]]
                #saving a class-global scope version of these variables for use in saving
                self.group1 = self.dataSet_inst.groupdict[re_match_list[0]]
                self.group2 = self.dataSet_inst.groupdict[re_match_list[1]]
            else:
                print 'Please use valid group labels'
                return
            if (group1.groupcount < 3) or (group2.groupcount < 3):  
                print "Must have 3 or more samples in each group"
                return
            for column in group1.columnavgs.keys():
                f_meandifference = abs(group1.columnavgs[column] - group2.columnavgs[column])
                #uses unequal variance
                #~ print "group1"
                #~ print  "average = %s" % group1.columnavgs[column]
                #~ print "stddev = %s" % group1.columnstddev[column]
                #~ print "group2"
                #~ print  "average = %s" % group2.columnavgs[column]
                #~ print "stddev = %s" % group2.columnstddev[column]
                se1 = (group1.columnstddev[column]**2)/(group1.groupcount)
                se2 = (group2.columnstddev[column]**2)/(group2.groupcount)
                f_tvalue = f_meandifference/math.sqrt(se1+se2)
                print "number = %s" % column
                print self.dataSet_inst.rowdict[0][column]
                throwaway, p_value = stats.F_oneway(group1.columndict[column],group2.columndict[column])
                print p_value
                if p_value < float(self.pvalcriteria):
                    #~ print "append this"
                    print
                    #~ print "p_value = %s and self.pvalcriteria = %s" % (p_value, self.pvalcriteria)
                    self.extractable_columns.append(column)
                else:
                    print 
                    #~ print "do not append"
                    #~ print "p_value = %s and self.pvalcriteria = %s" % (p_value, self.pvalcriteria)
                    
        
        else:
            print "Your input was not formatted correctly, please read the instructions"
            return None
        self.t_test_performed = True
        
    def run_kmeans(self, largs= [], kargs={}):
        #check to see if keywords are supplied. If they are, then exit conditional and proceed with the rest of the program, otherwise, check if interactive mod is active, if it is then ask the user for missing input
        #if it isn't active, then return at this point after calling an error message
        print "entering kmeans"

        if 'groups' in kargs.keys():
            centroid_num = int(kargs['groups'])
            
        self.l_array_row_identifier = []
        temp_list = []
        for (row_num, row) in self.dataSet_inst.rowdict.items():
            if row_num != 0:
                self.l_array_row_identifier.append(row_num)
                row_float = [float(x) for x in row[2:]]
                temp_list.append(row_float)
        os.chdir(self.rootdir)
        self.row_array = array(temp_list)
        self.whiten_array = whiten(self.row_array)
        self.kmeans_return_codebook, self.kmeans_distortion = kmeans(obs=self.whiten_array, k_or_guess=centroid_num, iter =30)
        self.vq_return_codebook, dist_throwaway = vq(self.whiten_array, self.kmeans_return_codebook)
        print self.vq_return_codebook
        i = 0
        if len(self.l_array_row_identifier) != len(self.vq_return_codebook):
            return
        try:
                os.mkdir(os.path.join(os.getcwd(),'kmeans'))
                os.chdir(os.path.join(os.getcwd(),'kmeans'))
        except:
                os.chdir(os.path.join(os.getcwd(),'kmeans'))
        try:   
            kmeans_file = open("kmeans.csv","wb")
            kmeans_csv = csv.writer(kmeans_file)
        except:
            print "Can't save kmeans file"
            return
        for number in self.l_array_row_identifier:
            
            print "%s is in cluster:%s" % (self.dataSet_inst.rowdict[number][0],self.vq_return_codebook[i])
            #writing of file goes here
            kmeans_csv.writerow([self.dataSet_inst.rowdict[number][0], self.vq_return_codebook[i]])
            
            i+=1
            
        if kargs:
            if self.required_arguments['run_kmeans'] in kargs.keys():
                #all the required arguments are found in the kargs
                print "all required arguments found"
        if self.interactivemode:
            print "PCA procedure initiated.\n"
        
    def run_pca(self, largs=[], kargs={}):
        req_arguments = ['axis1','axis2', 'color1', 'color2']
        #testing out the default dict paradigm
        #copied temp_list creator from another method, will add this to run and remove it from run_pca and kmeans later
        self.l_array_row_identifier = []
        temp_list = []
        if type(self.row_array)  !='numpy.ndarray':
                for (row_num, row) in self.dataSet_inst.rowdict.items():
                    if row_num != 0:

                        self.l_array_row_identifier.append(row_num)
                        row_float = [float(x) for x in row[2:]]
                        temp_list.append(row_float)

                self.row_array = array(temp_list)

        pca_inst = PCA(self.row_array)
        print pca_inst.Y
        if self.interactivemode:
            inputz = " "
            while "quit" not in inputz:
                print "which graph do you want to see? space out values with a space, each value should be an integer corresponding to an eigenvector"
                inputz = raw_input("$")
                input_list = re.findall("(\d{1,3})[ ]*",inputz)
                print input_list
                if len(input_list) ==2:
                    
                    scatter((-1*pca_inst.Y[:,input_list[0]]),(-1*pca_inst.Y[:,input_list[1]]))   
                    show()
                    close()
                elif len(input_list) == 3:
                    from mpl_toolkits.mplot3d import Axes3D
                    import matplotlib.pyplot as plt
                    fig = plt.figure()
                    ax = fig.add_subplot(111, projection='3d')
                    ax.scatter((-1*pca_inst.Y[:,input_list[0]]),(-1*pca_inst.Y[:,input_list[1]]), pca_inst.Y[:,input_list[2]])
                    show()
                    view_list = [30,50,60,100]
                    print "views do you want to see? must be angles between 0 and 360, alternatively, one can specify a range (increments in this range are restricted to 10"
                    view_input = raw_input("$")
                    view_list = re.findall("(\d{1,3})[ ]*",view_input)
                    if view_list:
                        for x in view_list:
                            x = float(x)
                            ax.view_init(30,x)
                            plt.draw()
                            fig.savefig(os.path.join(self.rootdir,str(int(x))+'.png'), format='png')
                            clf()
                            close()
                            

                    close()
                else:
                    print "use 2 or 3 eigenvectors"
        else:
            #gotta move this to its own function eventually (colorstuff)
            colordict = {}
            print kargs.keys()
            colorlist = [kargs[x] for x in kargs.keys() if 'color' in x]
            print colorlist
            for group in self.dataSet_inst.grouplist:
                if len(colorlist) == 0:
                    print "Not enough colors for groups"
                    return
                else:
                    
                    colordict[group] = colorlist.pop()
            colorarg = [colordict[x] for x in self.dataSet_inst.group_column]
            print colordict
            #we are running in a non-interactive mode
            for option in req_arguments:
                if option not in kargs.keys():
                    errorReporter.karg_error()
                    return
            if set(['axis1','axis2','axis3']).issubset(kargs.keys()):
                #we are in a 3d graph
                if set(['low','high','increment']).issubset(kargs.keys()):
                    #we are doing a range of 3d values
                    view_list = range(int(kargs['low']),int(kargs['high']),int(kargs['increment']))
                else:
                    view_list = None
                
                from mpl_toolkits.mplot3d import Axes3D
                import matplotlib.pyplot as plt
                fig = plt.figure()
                ax = fig.add_subplot(111, projection='3d')
                print "len = %s" %len(pca_inst.Y[1,:])
                ax.set_xlabel('PCA ' + str(int(kargs['axis1'])))
                ax.set_ylabel('PCA ' + str(int(kargs['axis2'])))
                ax.set_zlabel('PCA ' + str(int(kargs['axis3'])))
               
                ax.scatter(pca_inst.Y[:, int(kargs['axis1'])-1],pca_inst.Y[:,int(kargs['axis2'])-1], pca_inst.Y[:,int(kargs['axis3'])-1],c=colorarg)

                
                if view_list:
                    try:
                            os.mkdir(os.path.join(os.getcwd(),'pca3d'))
                            os.chdir(os.path.join(os.getcwd(),'pca3d'))
                    except:
                            os.chdir(os.path.join(os.getcwd(),'pca3d'))
                    for x in view_list:
                        x = float(x)
                        ax.view_init(30,x)
                        plt.draw()
                        
                        f_name = 'pca3d'+'view_'+(str(int(x)))+'pca_'+kargs['axis1']+'pca_'+kargs['axis2']+'pca_'+kargs['axis3']+'.png'
                        fig.savefig(os.path.join(os.getcwd(),f_name), format='png')

                        close()
                
                
            else:
                print "req_args"
                #~ colordict = {}
                #~ self.dataSet_inst.grouplist
                import matplotlib.pyplot as plt
                fig = plt.figure()
                ax=fig.add_subplot(111)
                print len(pca_inst.Y[:,0])
                print len(colorarg)
                try:
                    os.mkdir(os.path.join(self.rootdir,'pca2d'))
                    os.mkdir(os.path.join(self.rootdir,'pca2d'))
                except:
                    os.chdir(os.path.join(self.rootdir,'pca2d'))
                ax.set_xlabel('PCA ' + str(int(kargs['axis1'])))
                ax.set_ylabel('PCA ' + str(int(kargs['axis2'])))
                scatter((-1*pca_inst.Y[:,int(kargs['axis1'])-1]),(-1*pca_inst.Y[:,int(kargs['axis2'])-1]),c=colorarg)   
                fig.savefig(os.path.join(os.getcwd(),'pca2d'+'_pca'+kargs['axis1']+'_pca'+kargs['axis2']+'.png'), format='png')

                close()
            os.chdir(self.rootdir)
            print os.getcwd()
class statGroup:
    #contains all the data for a statistically relevant group, as determined from dataSet
    def __init__(self,group):
        self.group=group
        self.datalist = []
        #similar to rowcount but for the samples in the group
        self.groupcount = 0
        
        self.columncount = 0
        self.columnavgs = {}
        self.columnstddev = {}

    def report_membership(self):
        for i in range(0,self.groupcount):
            print self.datalist[i][0]
        
    def form_columndict(self):
        columndict= {}
        for columnnum in range(2,self.columncount): 
            tempcolumn = []
            for samplenum in range(0,self.groupcount):
                print self.datalist[samplenum][columnnum]
                tempcolumn.append(float(self.datalist[samplenum][columnnum]))
            columndict[columnnum] = tempcolumn
        self.columndict = columndict
class dataSet:
    #handles the entire dataset and generates statGroup objects to handle the individual groups
    def __init__(self):
        self.rowdict = {}
        self.columncount = 0
        self.columnavgs = {}
        self.groupdict = {}
        self.t_testdict = {}
        self.group_column= []
    def find_groups(self):

        grouplist = []
        for i in xrange(1,self.rowcount):
            grouplist.append(self.rowdict[i][1])

        self.grouplist=list(set(grouplist))
        
        #generate a new object for each unique group
        for group in self.grouplist:
            self.groupdict[group] = statGroup(group)
            self.groupdict[group].columncount = self.columncount
        #walk through each row and then add it to the correct datalist attribute of each statGroup, correspondingly
        for i in xrange(1,self.rowcount):
            self.groupdict[self.rowdict[i][1]].datalist.append(self.rowdict[i])
            self.groupdict[self.rowdict[i][1]].groupcount +=1
        for group in self.grouplist:
            self.groupdict[group].form_columndict()
            #self.groupdict[group].report_membership()


    

if __name__ == "__main__":
    s_readin = ' '
    kargs = {}
    commandCenter_inst = commandCenter()
    commandCenter_inst.interactivemode = False
    commandCenter_inst.scriptname='script.txt'
    f = open('script.txt','rb')
    
    for line in f:
        commandCenter_inst.command(line)
    #~ commandCenter_inst.command(" #load --filename=derp2.csv")
    #~ commandCenter_inst.command("load --filename=derp2.csv")
    #~ commandCenter_inst.run()
    #~ commandCenter_inst.command("box_plot --group1=vv --group2=dd")
    #~ commandCenter_inst.command("pca --axis1=1 --axis2=2 --color1=red --color2=green --low=10 --high=200 --increment=10")
    #~ while "quit" not in s_readin:
        #~ print "Commandlist: %s" % (', '.join(commandCenter_inst.report(),))
        #~ s_readin = raw_input("$")
        #~ commandCenter_inst.command(s_readin)
    
    