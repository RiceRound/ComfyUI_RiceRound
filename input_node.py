_X='number'
_W='bridge'
_V='only image.'
_U='load_image'
_T='prompt'
_S='unique_id'
_R='BOOLEAN'
_Q='str'
_P='MASK'
_O='tooltip'
_N='hidden'
_M='数值'
_L='IMAGE'
_K='optional'
_J='FLOAT'
_I='load'
_H='INT'
_G='name'
_F='value'
_E='required'
_D=True
_C='RiceRound/Input'
_B='STRING'
_A='default'
import hashlib,json,os,re,time,random
from PIL import Image,ImageOps
from PIL.PngImagePlugin import PngInfo
from.rice_prompt_info import RicePromptInfo
import folder_paths
from nodes import LoadImage
import requests,sys
from.utils import pil2tensor
from comfy.utils import ProgressBar
class _BasicTypes(str):
	basic_types=[_B]
	def __eq__(B,other):A=other;return A in B.basic_types or isinstance(A,(list,_BasicTypes))
	def __ne__(A,other):return not A.__eq__(other)
BasicTypes=_BasicTypes('BASIC')
class RiceRoundSimpleChoiceNode:
	def __init__(A):A.prompt_info=RicePromptInfo()
	@classmethod
	def INPUT_TYPES(A):return{_E:{_G:(_B,{_A:'Parameter'}),_A:(_B,{_A:''})},_K:{},_N:{_S:'UNIQUE_ID',_T:'PROMPT','extra_pnginfo':'EXTRA_PNGINFO'}}
	RETURN_TYPES=BasicTypes,;RETURN_NAMES=_F,;FUNCTION='placeholder';CATEGORY=_C
	def placeholder(B,name,default,**C):
		A=int(C.pop(_S,0));D=C.pop(_T,None);E=_D
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
class RiceRoundSimpleImageNode(LoadImage):
	def __init__(A):super().__init__()
	RETURN_TYPES=_L,;RETURN_NAMES=_F,;OUTPUT_NODE=_D;CATEGORY=_C;FUNCTION=_U
	def load_image(B,image):A,C=super().load_image(image);return A,
class RiceRoundDownloadImageNode:
	def __init__(A):0
	@classmethod
	def INPUT_TYPES(A):return{_E:{'image_url':(_B,{_A:''})},_K:{},_N:{}}
	RETURN_TYPES=_L,;RETURN_NAMES=_F,;OUTPUT_NODE=_D;FUNCTION=_U;CATEGORY=_C
	def load_image(B,image_url,**C):A=Image.open(requests.get(image_url,stream=_D).raw);A=ImageOps.exif_transpose(A);return pil2tensor(A),
class RiceRoundImageBridgeNode:
	def __init__(A):0
	@classmethod
	def INPUT_TYPES(A):return{_E:{'images':(_L,{_O:_V})},_K:{}}
	RETURN_TYPES=_L,;RETURN_NAMES=_F,;OUTPUT_NODE=_D;FUNCTION=_W;CATEGORY=_C
	def bridge(A,images,**B):return images,
class RiceRoundMaskBridgeNode:
	def __init__(A):0
	@classmethod
	def INPUT_TYPES(A):return{_E:{'mask':(_P,{_O:_V})}}
	RETURN_TYPES=_P,;RETURN_NAMES=_F,;OUTPUT_NODE=_D;FUNCTION=_W;CATEGORY=_C
	def bridge(A,mask,**B):return mask,
class RiceRoundDownloadMaskNode:
	def __init__(A):0
	@classmethod
	def INPUT_TYPES(A):return{_E:{'mask_url':(_B,{_A:''})}}
	RETURN_TYPES=_P,;RETURN_NAMES=_F,;OUTPUT_NODE=_D;FUNCTION='load_mask';CATEGORY=_C
	def load_mask(E,mask_url,**F):
		C=mask_url
		try:
			D=requests.get(C,stream=_D,timeout=10);D.raise_for_status();A=Image.open(D.raw)
			if A.mode!='L':A=A.convert('L')
			return pil2tensor(A),
		except requests.exceptions.RequestException as B:print(f"Error downloading mask from {C}: {str(B)}");raise
		except Exception as B:print(f"Error processing mask: {str(B)}");raise
class RiceRoundIntNode:
	def __init__(A):0
	@classmethod
	def INPUT_TYPES(A):return{_E:{_G:(_B,{_A:_M}),_X:(_H,{_A:0}),'min':(_H,{_A:0}),'max':(_H,{_A:100})}}
	RETURN_TYPES=_H,;RETURN_NAMES=_F,;OUTPUT_NODE=_D;FUNCTION=_I;CATEGORY=_C
	def load(A,name,number,min,max,**B):return number,
class RiceRoundStrToIntNode:
	def __init__(A):0
	@classmethod
	def INPUT_TYPES(A):return{_E:{_G:(_B,{_A:_M}),_Q:(_B,)}}
	RETURN_TYPES=_H,;RETURN_NAMES=_F,;OUTPUT_NODE=_D;FUNCTION=_I;CATEGORY=_C
	def load(A,name,str,**B):return int(str),
class RiceRoundFloatNode:
	def __init__(A):0
	@classmethod
	def INPUT_TYPES(A):return{_E:{_G:(_B,{_A:_M}),_X:(_J,{_A:.0}),'min':(_J,{_A:.0}),'max':(_J,{_A:1e2})}}
	RETURN_TYPES=_J,;RETURN_NAMES=_F,;OUTPUT_NODE=_D;FUNCTION=_I;CATEGORY=_C
	def load(A,name,number,min,max,**B):return number,
class RiceRoundStrToFloatNode:
	def __init__(A):0
	@classmethod
	def INPUT_TYPES(A):return{_E:{_G:(_B,{_A:_M}),_Q:(_B,)}}
	RETURN_TYPES=_J,;RETURN_NAMES=_F,;OUTPUT_NODE=_D;FUNCTION=_I;CATEGORY=_C
	def load(A,name,str,**B):return float(str),
class RiceRoundBooleanNode:
	@classmethod
	def INPUT_TYPES(A):return{_E:{_G:(_B,{_A:'开关'}),_F:(_R,{_A:False})}}
	RETURN_TYPES=_R,;RETURN_NAMES=_F,;FUNCTION='execute';CATEGORY=_C
	def execute(A,name,value):return value,
class RiceRoundStrToBooleanNode:
	def __init__(A):0
	@classmethod
	def INPUT_TYPES(A):return{_E:{_G:(_B,{_A:'开关'}),_Q:(_B,)}}
	RETURN_TYPES=_R,;RETURN_NAMES=_F,;OUTPUT_NODE=_D;FUNCTION=_I;CATEGORY=_C
	def load(A,name,str,**B):return str.lower()=='true',
class RiceRoundInputTextNode:
	def __init__(A):0
	@classmethod
	def INPUT_TYPES(A):return{_E:{'text_info':(_B,{'multiline':_D,_O:'The text to be encoded.'})}}
	RETURN_TYPES=_B,;OUTPUT_NODE=_D;FUNCTION=_I;CATEGORY=_C
	def load(D,text_info,**E):
		B=text_info;A=''
		try:C=json.loads(B);A=C.get('content','')
		except json.JSONDecodeError:A=B
		return A,
class RiceRoundRandomSeedNode:
	def __init__(A):0
	@classmethod
	def INPUT_TYPES(A):return{_E:{},_K:{},_N:{}}
	RETURN_TYPES=_H,;FUNCTION='random';CATEGORY=_C
	@classmethod
	def IS_CHANGED(A):return random.randint(0,999999)
	def random(B):A=random.randint(0,999999);print('产生随机数 ',A);return A,
class RiceRoundDebugNode:
	def __init__(A):0
	@classmethod
	def INPUT_TYPES(A):return{_E:{'text':(_B,{_A:'Hello, World!'})}}
	RETURN_TYPES=_B,;FUNCTION='debug';CATEGORY=_C
	def debug(A,text):print(f"RiceDebugNode text: {text}");return text,