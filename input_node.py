_a='number'
_Z='bridge'
_Y='only image.'
_X='image_url'
_W='prompt'
_V='unique_id'
_U='BOOLEAN'
_T='str'
_S='tooltip'
_R='mask'
_Q='hidden'
_P='数值'
_O='load_image'
_N=None
_M='optional'
_L='FLOAT'
_K='MASK'
_J='load'
_I='INT'
_H='IMAGE'
_G='name'
_F='value'
_E='required'
_D='RiceRound/Input'
_C='STRING'
_B=True
_A='default'
import hashlib,json,os,re,time,random
from PIL import Image,ImageOps,ImageSequence
import numpy as np,torch,node_helpers
from.rice_prompt_info import RicePromptInfo
from nodes import LoadImage
import requests
from.utils import pil2tensor
class _BasicTypes(str):
	basic_types=[_C]
	def __eq__(B,other):A=other;return A in B.basic_types or isinstance(A,(list,_BasicTypes))
	def __ne__(A,other):return not A.__eq__(other)
BasicTypes=_BasicTypes('BASIC')
class RiceRoundSimpleChoiceNode:
	def __init__(A):A.prompt_info=RicePromptInfo()
	@classmethod
	def INPUT_TYPES(A):return{_E:{_G:(_C,{_A:'Parameter'}),_A:(_C,{_A:''})},_M:{},_Q:{_V:'UNIQUE_ID',_W:'PROMPT','extra_pnginfo':'EXTRA_PNGINFO'}}
	RETURN_TYPES=BasicTypes,;RETURN_NAMES=_F,;FUNCTION='placeholder';CATEGORY=_D
	def placeholder(B,name,default,**C):
		A=int(C.pop(_V,0));D=C.pop(_W,_N);E=_B
		if D:
			for(G,F)in D.items():
				if F.get('class_type','')=='RiceRoundDecryptNode':E=False;break
		if E:
			for H in range(10):
				if A in B.prompt_info.choice_node_map:break
				time.sleep(1)
		if A not in B.prompt_info.choice_node_map:print(f"Warning: RiceRoundSimpleChoiceNode {A} not found in prompt_info.choice_node_map")
		return default,
class RiceRoundAdvancedChoiceNode(RiceRoundSimpleChoiceNode):
	def __init__(A):super().__init__()
	CATEGORY='RiceRound/Advanced'
class RiceRoundSimpleImageNode(LoadImage):
	def __init__(A):super().__init__()
	RETURN_TYPES=_H,;RETURN_NAMES=_F,;OUTPUT_NODE=_B;CATEGORY=_D;FUNCTION=_O
	def load_image(B,image):A,C=super().load_image(image);return A,
class RiceRoundImageNode(LoadImage):
	def __init__(A):super().__init__()
	RETURN_TYPES=_H,_K;RETURN_NAMES='image',_R;OUTPUT_NODE=_B;CATEGORY=_D;FUNCTION=_O
	def load_image(A,image):return super().load_image(image)
class RiceRoundDownloadImageNode:
	def __init__(A):0
	@classmethod
	def INPUT_TYPES(A):return{_E:{_X:(_C,{_A:''})},_M:{},_Q:{}}
	RETURN_TYPES=_H,;RETURN_NAMES=_F,;OUTPUT_NODE=_B;FUNCTION=_O;CATEGORY=_D
	def load_image(B,image_url,**C):A=Image.open(requests.get(image_url,stream=_B).raw);A=ImageOps.exif_transpose(A);return pil2tensor(A),
class RiceRoundDownloadImageAndMaskNode:
	def __init__(A):0
	@classmethod
	def INPUT_TYPES(A):return{_E:{_X:(_C,{_A:''})}}
	RETURN_TYPES=_H,_K;RETURN_NAMES='image',_R;OUTPUT_NODE=_B;FUNCTION=_O;CATEGORY=_D
	def load_image(L,image_url,**M):
		D=Image.open(requests.get(image_url,stream=_B).raw);D=ImageOps.exif_transpose(D);C=[];F=[];G,H=_N,_N;K=['MPO']
		for B in ImageSequence.Iterator(D):
			B=node_helpers.pillow(ImageOps.exif_transpose,B)
			if B.mode=='I':B=B.point(lambda i:i*(1/255))
			A=B.convert('RGB')
			if len(C)==0:G=A.size[0];H=A.size[1]
			if A.size[0]!=G or A.size[1]!=H:continue
			A=np.array(A).astype(np.float32)/255.;A=torch.from_numpy(A)[_N,]
			if'A'in B.getbands():E=np.array(B.getchannel('A')).astype(np.float32)/255.;E=1.-torch.from_numpy(E)
			else:E=torch.zeros((64,64),dtype=torch.float32,device='cpu')
			C.append(A);F.append(E.unsqueeze(0))
		if len(C)>1 and D.format not in K:I=torch.cat(C,dim=0);J=torch.cat(F,dim=0)
		else:I=C[0];J=F[0]
		return I,J
class RiceRoundImageBridgeNode:
	def __init__(A):0
	@classmethod
	def INPUT_TYPES(A):return{_E:{'images':(_H,{_S:_Y})},_M:{}}
	RETURN_TYPES=_H,;RETURN_NAMES=_F,;OUTPUT_NODE=_B;FUNCTION=_Z;CATEGORY=_D
	def bridge(A,images,**B):return images,
class RiceRoundMaskBridgeNode:
	def __init__(A):0
	@classmethod
	def INPUT_TYPES(A):return{_E:{_R:(_K,{_S:_Y})}}
	RETURN_TYPES=_K,;RETURN_NAMES=_F,;OUTPUT_NODE=_B;FUNCTION=_Z;CATEGORY=_D
	def bridge(A,mask,**B):return mask,
class RiceRoundDownloadMaskNode:
	def __init__(A):0
	@classmethod
	def INPUT_TYPES(A):return{_E:{'mask_url':(_C,{_A:''})}}
	RETURN_TYPES=_K,;RETURN_NAMES=_F,;OUTPUT_NODE=_B;FUNCTION='load_mask';CATEGORY=_D
	def load_mask(E,mask_url,**F):
		C=mask_url
		try:
			D=requests.get(C,stream=_B,timeout=10);D.raise_for_status();A=Image.open(D.raw)
			if A.mode!='L':A=A.convert('L')
			return pil2tensor(A),
		except requests.exceptions.RequestException as B:print(f"Error downloading mask from {C}: {str(B)}");raise
		except Exception as B:print(f"Error processing mask: {str(B)}");raise
class RiceRoundIntNode:
	def __init__(A):0
	@classmethod
	def INPUT_TYPES(A):return{_E:{_G:(_C,{_A:_P}),_a:(_I,{_A:0}),'min':(_I,{_A:0}),'max':(_I,{_A:100})}}
	RETURN_TYPES=_I,;RETURN_NAMES=_F,;OUTPUT_NODE=_B;FUNCTION=_J;CATEGORY=_D
	def load(A,name,number,min,max,**B):return number,
class RiceRoundStrToIntNode:
	def __init__(A):0
	@classmethod
	def INPUT_TYPES(A):return{_E:{_G:(_C,{_A:_P}),_T:(_C,)}}
	RETURN_TYPES=_I,;RETURN_NAMES=_F,;OUTPUT_NODE=_B;FUNCTION=_J;CATEGORY=_D
	def load(A,name,str,**B):return int(str),
class RiceRoundFloatNode:
	def __init__(A):0
	@classmethod
	def INPUT_TYPES(A):return{_E:{_G:(_C,{_A:_P}),_a:(_L,{_A:.0}),'min':(_L,{_A:.0}),'max':(_L,{_A:1e2})}}
	RETURN_TYPES=_L,;RETURN_NAMES=_F,;OUTPUT_NODE=_B;FUNCTION=_J;CATEGORY=_D
	def load(A,name,number,min,max,**B):return number,
class RiceRoundStrToFloatNode:
	def __init__(A):0
	@classmethod
	def INPUT_TYPES(A):return{_E:{_G:(_C,{_A:_P}),_T:(_C,)}}
	RETURN_TYPES=_L,;RETURN_NAMES=_F,;OUTPUT_NODE=_B;FUNCTION=_J;CATEGORY=_D
	def load(A,name,str,**B):return float(str),
class RiceRoundBooleanNode:
	@classmethod
	def INPUT_TYPES(A):return{_E:{_G:(_C,{_A:'开关'}),_F:(_U,{_A:False})}}
	RETURN_TYPES=_U,;RETURN_NAMES=_F,;FUNCTION='execute';CATEGORY=_D
	def execute(A,name,value):return value,
class RiceRoundStrToBooleanNode:
	def __init__(A):0
	@classmethod
	def INPUT_TYPES(A):return{_E:{_G:(_C,{_A:'开关'}),_T:(_C,)}}
	RETURN_TYPES=_U,;RETURN_NAMES=_F,;OUTPUT_NODE=_B;FUNCTION=_J;CATEGORY=_D
	def load(A,name,str,**B):return str.lower()=='true',
class RiceRoundInputTextNode:
	def __init__(A):0
	@classmethod
	def INPUT_TYPES(A):return{_E:{'text_info':(_C,{'multiline':_B,_S:'The text to be encoded.'})}}
	RETURN_TYPES=_C,;OUTPUT_NODE=_B;FUNCTION=_J;CATEGORY=_D
	def load(D,text_info,**E):
		B=text_info;A=''
		try:C=json.loads(B);A=C.get('content','')
		except json.JSONDecodeError:A=B
		return A,
class RiceRoundRandomSeedNode:
	def __init__(A):0
	@classmethod
	def INPUT_TYPES(A):return{_E:{},_M:{},_Q:{}}
	RETURN_TYPES=_I,;FUNCTION='random';CATEGORY=_D
	@classmethod
	def IS_CHANGED(A):return random.randint(0,999999)
	def random(B):A=random.randint(0,999999);print('产生随机数 ',A);return A,