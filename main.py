"""
This is a test/demo of the terrain system.

"""

from panda3d.core import *

loadPrcFile("TerrainConfig.prc")

from direct.showbase.ShowBase import ShowBase
from direct.showbase.DirectObject import DirectObject
import direct.directbase.DirectStart
from direct.filter.CommonFilters import CommonFilters
import math
from direct.task import Task
from direct.gui.OnscreenText import OnscreenText
from direct.actor.Actor import Actor
import sys

import terrain
import terrain.bakery.animate_dreams_bakery
import terrain.bakery.gpuBakery
from terrain.renderer.renderer import RenderNode
from terrain.renderer.renderTiler import RenderTileBakery,RenderNodeTiler
from terrain.renderer.geoClipMapper import GeoClipMapper
from terrain.bakery.bakery import loadTex
import water

import terrain.meshManager.meshManager
import terrain.meshManager.treeFactory
import terrain.meshManager.fernFactory
import terrain.meshManager.groundFactory


print PandaSystem.getVersionString()
backBinName="background"

dataDir="data/"

############## Configure! ##############
#rendererClass=GeoClipMapper
rendererClass=RenderTileBakery
if rendererClass==RenderTileBakery:
    #selectedBakery = terrain.bakery.animate_dreams_bakery.ADBakery ; rendererFolder=dataDir+'renderTilerSimple'
    selectedBakery = terrain.bakery.gpuBakery.GpuBakery ; rendererFolder=dataDir+'renderTiler'
mouseControl=False
enableWater=True
############## Configure! ##############




# Init camera
base.disableMouse()
camLens=base.camLens
camLens.setNear(1)

maxDist=10000

camLens.setFar(maxDist*20)
base.cam.node().setLens(camLens)


tileSize=200.0
terrainScale=1.0

focus=NodePath("tilerFocuse")

if rendererClass is GeoClipMapper:
    # Create a bakery that uses the "bakery2" folder for its resources
    b=terrain.bakery.gpuBakery.GpuBakery(None,dataDir+"bakeryData")
    n=GeoClipMapper(dataDir+'renderData',b,tileSize/4.0,focus)
    if enableWater: waterNode = water.WaterNode( -10, -10, 20, 20, .01)
else:
    
    # Create a bakery that uses the "bakeryTiler" folder for its resources
    b = selectedBakery(None,dataDir+"bakeryTiler")
    #Make the main (highest LOD) tiler
    barkTexture=loader.loadTexture(dataDir+"textures/barkTexture.jpg")
    leafTexture=loader.loadTexture(dataDir+"textures/material-10-cl.png")
    tf=terrain.meshManager.treeFactory.TreeFactory(barkTexture=barkTexture,leafTexture=leafTexture)
    ff=terrain.meshManager.fernFactory.FernFactory(leafTexture)
    heightScale=300
    gf=terrain.meshManager.groundFactory.GroundFactory(rendererFolder,heightScale=heightScale)
    
    factories=[gf,ff,tf]
    
    LODCutoffs=[float('inf'),2000,1000,500,300]

    meshManager=terrain.meshManager.meshManager.MeshManager(factories)
    rtb=RenderTileBakery(b,tileSize,meshManager,heightScale)
    
    n=RenderNodeTiler(rtb,tileSize,focus,forceRenderedCount=2,maxRenderedCount=6,)
    
    #x=RenderNode(rendererFolder,n)
    
    #n=rendererClass(rendererFolder,b,tileSize,focus,factories,2,3,heightScale=300)
    if enableWater: waterNode = water.WaterNode( -100, -100, 200, 200, 0.1*heightScale)
    


    
    
n.reparentTo(render)
n.setScale(terrainScale)



base.setBackgroundColor(.3,.3,.8,0)

# Make a little UI input handeling class
class UI(DirectObject):
    def __init__(self):
        self.accept("v", base.bufferViewer.toggleEnable)
        self.accept("x", self.analize)
        self.accept("o", base.toggleWireframe)
        self.accept("u", base.oobe)
        self.accept("y", base.oobeCull)
        
        
        base.bufferViewer.setPosition("llcorner")
        base.bufferViewer.setCardSize(.25, 0.0)

            
    def analize(self):
        print ""
        render.analyze()
        print ""
        render.ls()
        print ""

ui=UI()


dlight = DirectionalLight('dlight')

dlnp = render.attachNewNode(dlight)
dlnp.setHpr(0, 0, 0)
render.setLight(dlnp)

alight = AmbientLight('alight')

alnp = render.attachNewNode(alight)
render.setLight(alnp)

#rotating light to show that normals are calculated correctly
def updateLight(task):    
    h=task.time/30.0*360+180
    
    dlnp.setHpr(0,h,0)
    h=h+90
    h=h%360
    h=min(h,360-h)
    #h is now angle from straight up
    hv=h/180.0
    hv=1-hv
    sunset=max(0,1.0-abs(hv-.5)*8)
    sunset=min(1,sunset)
    if hv>.5: sunset=1
    #sunset=sunset**.2
    sunset=VBase4(0.8, 0.5, 0.0, 1)*sunset
    sun=max(0,hv-.5)*2*4
    sun=min(sun,1)
    dColor=(VBase4(0.8, 0.7, 0.7, 1)*sun*2+sunset)
    dlight.setColor(dColor)
    aColor=VBase4(0.3, 0.3, 0.8, 1)*sun*2.6+VBase4(0.2, 0.2, 0.4, 1)*2.0
    alight.setColor(aColor*(8-dColor.length())*(1.0/8))
    return Task.cont    

taskMgr.add(updateLight, "rotating Light")





# skybox
skybox = loader.loadModel(dataDir+'models/skybox.egg')
# make big enough to cover whole terrain, else there'll be problems with the water reflections
skybox.setScale(maxDist*3)
skybox.setBin('background', 1)
skybox.setDepthWrite(0)
skybox.setLightOff()
skybox.reparentTo(render)

# Filter to display the glow map's glow via bloom.
filters = CommonFilters(base.win, base.cam)
#filterok = filters.setBloom(blend=(0,0,0,1), desat=0.5, intensity=2.5, size="small",mintrigger=0.0, maxtrigger=1.0)




font = TextNode.getDefaultFont()

# Function to put instructions on the screen.
def addInstructions(pos, msg):
    return OnscreenText(text=msg, style=1, fg=(1,1,1,1), font = font,
                        pos=(-1.3, pos), align=TextNode.ALeft, scale = .05)

# Function to put title on the screen.
def addTitle(text):
    return OnscreenText(text=text, style=1, fg=(1,1,1,1), font = font,
                        pos=(1.3,-0.95), align=TextNode.ARight, scale = .07)
#A simple function to make sure a value is in a given range, -1 to 1 by default
def restrain(i, mn = -1, mx = 1): return min(max(i, mn), mx)


class keyTracker(DirectObject):
    """
    Class for tracking the state of keys. keyMap holds if a key is down
    Multiple keys can map to one name, though the value will be set to false when the first is relased
    """
    def __init__(self):
        DirectObject.__init__(self)
        self.keyMap = {}
        
    def setKey(self, key, value):
        """Records the state of key"""
        self.keyMap[key] = value
    
    def addKey(self,key,name,allowShift=True):
        self.accept(key, self.setKey, [name,True])
        self.accept(key+"-up", self.setKey, [name,False])  
        self.accept(key.upper()+"-up", self.setKey, [name,False])
        
        if allowShift:
            self.addKey("shift-"+key,name,False)
        
        self.keyMap[name]=False
        

class World(keyTracker):
    def __init__(self):
        keyTracker.__init__(self)
        
        base.win.setClearColor(Vec4(0,0,0,1))

        # Post the instructions

        self.title = addTitle("Infinite Ralph")
        self.inst1 = addInstructions(0.95, "[ESC]: Quit")
        self.inst2 = addInstructions(0.90, "WASD + Mouse (Or arrow Keys)")
        self.inst3 = addInstructions(0.85, "Shift for hyper")
        self.inst3 = addInstructions(0.80, "X for analyze")
        self.inst3 = addInstructions(0.70, "V toggles buffer viewer")
        self.inst3 = addInstructions(0.65, "U toggles oobe")
        self.inst3 = addInstructions(0.60, "Y toggles oobeCull")
        self.inst3 = addInstructions(0.55, "O toggles Wireframe")
        
        # Create the main character, Ralph

        ralphStartPos = Vec3(0,0,0)
        self.ralph = Actor(dataDir+"models/ralph",{"run":dataDir+"models/ralph-run"})
        self.ralph.reparentTo(render)
        self.ralph.setScale(.4)
        self.ralph.setPos(ralphStartPos)
        #self.ralph.setShaderAuto()
        
        focus.reparentTo(self.ralph)

        # Create a floater object.  We use the "floater" as a temporary
        # variable in a variety of calculations.
        
        self.floater = NodePath(PandaNode("floater"))
        self.floater.reparentTo(self.ralph)

        # Accept the control keys for movement and rotation
        
        self.accept("escape", sys.exit)

        
        self.addKey("w","forward")
        self.addKey("a","left")
        self.addKey("s","backward")
        self.addKey("d","right")
        self.addKey("arrow_left","turnLeft")
        self.addKey("arrow_right","turnRight")
        self.addKey("arrow_down","turnDown")
        self.addKey("arrow_up","turnUp")
        
        self.setKey('zoom',0)
        self.accept("wheel_up", self.setKey, ['zoom',1])
        self.accept("wheel_down", self.setKey, ['zoom',-1])
        
        #addKey("wheel_down","zoomOut")
        #addKey("wheel_up","zoomIn")
        self.addKey("shift","hyper")

        taskMgr.add(self.move,"moveTask")

        # Game state variables
        self.isMoving = False

        # Set up the camera
        
        base.disableMouse()
        base.camera.setH(180)
        
        base.camera.reparentTo(self.ralph)
        self.camDist=0.0
        self.floater.setZ(6)
        self.floater.setY(-1)
        
        

        n.setShaderAuto()
            
    def move(self, task):

        # Get the time elapsed since last frame. We need this
        # for framerate-independent movement.
        elapsed = globalClock.getDt()
        if enableWater: waterNode.setShaderInput('time', task.time)
        # move the skybox with the camera
        campos = base.camera.getPos()
        skybox.setPos(campos)
        if enableWater: waterNode.update()
        
        
        turnRightAmount=self.keyMap["turnRight"]-self.keyMap["turnLeft"]
        turnUpAmmount=self.keyMap["turnUp"]-self.keyMap["turnDown"]
        
        turnRightAmount*=elapsed*100
        turnUpAmmount*=elapsed*100
        
        # Use mouse input to turn both Ralph and the Camera 
        if mouseControl and base.mouseWatcherNode.hasMouse(): 
            # get changes in mouse position 
            md = base.win.getPointer(0) 
            x = md.getX() 
            y = md.getY() 
            deltaX = md.getX() - 200 
            deltaY = md.getY() - 200 
            # reset mouse cursor position 
            base.win.movePointer(0, 200, 200) 
            
            turnRightAmount+=0.2* deltaX
            turnUpAmmount-= 0.2 * deltaY 
            
        zoomOut=self.keyMap["zoom"]
        self.camDist=max(min(maxDist,self.camDist+zoomOut*elapsed*50+zoomOut*self.camDist*elapsed*.5),.5)
        self.keyMap["zoom"]*=2.7**(-elapsed*4)# Smooth fade out of zoom speed
        
        
        self.ralph.setH(self.ralph.getH() - turnRightAmount)
        base.camera.setP(base.camera.getP() + turnUpAmmount)
        
        # save ralph's initial position so that we can restore it,
        # in case he falls off the map or runs into something.
        startpos = self.ralph.getPos()

        # If a move-key is pressed, move ralph in the specified direction.
        # Adding, subtracting and multiplying booleans for the keys here.
        forwardMove=self.keyMap["forward"]-.5*self.keyMap["backward"]
        rightMove=.5*(self.keyMap["right"]-self.keyMap["left"])
        
        # Slow forward when moving diagonal
        forwardMove*=1.0-abs(rightMove)
        
        # Hyper mode. Prabably just for debug
        speed=1+4*self.keyMap["hyper"]

        rightMove*=speed
        forwardMove*=speed
        
        self.ralph.setX(self.ralph, -elapsed*25*rightMove)
        self.ralph.setY(self.ralph, -elapsed*25*forwardMove)
        h=n.height(self.ralph.getX(n),self.ralph.getY(n))
        self.ralph.setZ(n,h)

        
        def sign(n):
            if n>=0: return 1
            #if n==0: return 0
            return -1
        
        # If ralph is moving, loop the run animation.
        # If he is standing still, stop the animation.
        if rightMove or forwardMove:
            self.ralph.setPlayRate(forwardMove+abs(rightMove)*sign(forwardMove), 'run')
            if self.isMoving is False:
                self.ralph.loop("run")
                
                #self.ralph.loop("walk")
                self.isMoving = True
        else:
            if self.isMoving:
                self.ralph.stop()
                self.ralph.pose("walk",5)
                self.isMoving = False

        # The camera should look in ralph's direction,
        # but it should also try to stay horizontal, so look at
        # a floater which hovers above ralph's head.
      
        
        base.camera.setPos(self.floater,0,0,0)
        base.camera.setPos(base.camera,0,-self.camDist,0)

        return Task.cont


w = World()
run()
