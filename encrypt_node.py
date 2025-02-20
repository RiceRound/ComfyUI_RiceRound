_z='Node name for S&R'
_y='properties'
_x='input_anything'
_w='main_link_type'
_v='last_node_id'
_u='owner_id'
_t='EXTRA_PNGINFO'
_s='PROMPT'
_r='UNIQUE_ID'
_q='project_name'
_p='hidden'
_o='required'
_n='RiceRoundInputTextNode'
_m='RiceRoundDecryptNode'
_l='title'
_k='main_link_id'
_j='slot_index'
_i='task_id'
_h='PNG'
_g='images'
_f='template_id'
_e='RiceRoundAdvancedChoiceNode'
_d='RiceRoundSimpleChoiceNode'
_c='_meta'
_b=True
_a='extra_pnginfo'
_Z='prompt'
_Y='RiceRoundStrToBooleanNode'
_X='RiceRoundBooleanNode'
_W='RiceRoundStrToFloatNode'
_V='RiceRoundStrToIntNode'
_U='RiceRoundFloatNode'
_T='RiceRoundIntNode'
_S='RiceRoundDownloadMaskNode'
_R='RiceRoundMaskBridgeNode'
_Q='RiceRoundImageBridgeNode'
_P='RiceRoundImageNode'
_O='RiceRoundSimpleImageNode'
_N='class_type'
_M='unique_id'
_L='RiceRoundDownloadImageNode'
_K='name'
_J='IMAGE'
_I='default'
_H='inputs'
_G='outputs'
_F='nodes'
_E='STRING'
_D='id'
_C='links'
_B=None
_A='type'
from collections import defaultdict
import copy
from io import BytesIO
import json,os,random,shutil,uuid,numpy as np,comfy.utils,time
from PIL import Image
from.rice_def import RiceRoundErrorDef
from.rice_install_client import RiceInstallClient
from.auth_unit import AuthUnit
from.publish import Publish
from.utils import combine_files
from.rice_url_config import machine_upload_image
import folder_paths
from server import PromptServer
from.rice_url_config import RiceUrlConfig
from.rice_prompt_info import RicePromptInfo
output_project_folder=folder_paths.output_directory
INPUT_NODE_TYPES=[_d,_e,_O,_P,_L,_Q,_n,_R,_S,_T,_U,_V,_W,_X,_Y]
class RiceRoundEncryptNode:
	def __init__(A):A.template_id=uuid.uuid4().hex;A.output_dir=folder_paths.get_temp_directory();A.type='temp';A.prefix_append='_temp_'+''.join(random.choice('abcdefghijklmnopqrstupvxyz')for A in range(5));A.compress_level=4
	@classmethod
	def INPUT_TYPES(A):return{_o:{_q:(_E,{_I:'my_project'}),_f:(_E,{_I:uuid.uuid4().hex}),_g:(_J,)},_p:{_M:_r,_Z:_s,_a:_t}}
	@classmethod
	def IS_CHANGED(A,**B):return float('NaN')
	RETURN_TYPES=();OUTPUT_NODE=_b;FUNCTION='encrypt';CATEGORY='RiceRound'
	def encrypt(B,project_name,template_id,images,**E):
		S='error';R='content';Q='riceround_toast';K=project_name;D=template_id;A=images;f=E.pop(_M,_B);T=E.pop(_a,_B);U=E.pop(_Z,_B);V=Encrypt(T['workflow'],U,K,D);F=V.do_encrypt();G='rice_round';G+=B.prefix_append;W,X,L,Y,G=folder_paths.get_save_image_path(G,B.output_dir,A[0].shape[1],A[0].shape[0]);M=list();Z=comfy.utils.ProgressBar(A.shape[0]);H=_B
		for(I,a)in enumerate(A):
			b=255.*a.cpu().numpy();J=Image.fromarray(np.clip(b,0,255).astype(np.uint8))
			if I==0:H=os.path.join(F,'preview.png');J.save(H)
			Z.update_absolute(I,A.shape[0],(_h,J,_B));c=X.replace('%batch_num%',str(I));N=f"{c}_{L:05}_.png";J.save(os.path.join(W,N),compress_level=B.compress_level);M.append({'filename':N,'subfolder':Y,_A:B.type});L+=1
		d=RicePromptInfo().get_auto_publish()
		if d:
			e=Publish(F);O,P,C=AuthUnit().get_user_token()
			if not O:
				print(f"riceround get user token failed, {P}")
				if C==RiceRoundErrorDef.HTTP_UNAUTHORIZED or C==RiceRoundErrorDef.NO_TOKEN_ERROR:AuthUnit().login_dialog('安装节点需要先完成登录')
				else:PromptServer.instance.send_sync(Q,{R:'无法完成鉴权登录，请检查网络或完成登录步骤',_A:S})
				return{}
			else:e.publish(O,D,K,H,os.path.join(F,f"{D}.bin"))
		if RicePromptInfo().get_run_client():
			C,P=RiceInstallClient().run_client()
			if C!=RiceRoundErrorDef.SUCCESS:PromptServer.instance.send_sync(Q,{R:'加密节点发布完成，但无法启动client，建议官网重新安装',_A:S})
		return{'ui':{_g:M}}
class RiceRoundOutputImageNode:
	def __init__(A):A.url_config=RiceUrlConfig()
	@classmethod
	def INPUT_TYPES(A):return{_o:{_g:(_J,),_i:(_E,{_I:''})},'optional':{_f:(_E,{_I:''})},_p:{_M:_r,_Z:_s,_a:_t}}
	RETURN_TYPES=();OUTPUT_NODE=_b;FUNCTION='load';CATEGORY='__hidden__'
	def load(N,images,task_id,template_id,**B):
		I='image_type';C=images;A=task_id;D=B.pop(_M,_B);J=B.pop(_Z,_B);O=B.pop(_a,_B);E=PromptServer.instance.client_id;F=''
		if hasattr(PromptServer.instance,'last_prompt_id')and PromptServer.instance.last_prompt_id:F=PromptServer.instance.last_prompt_id
		if D is _B:raise Exception("Warning: 'unique_id' is missing.")
		if J is _B:raise Exception("Warning: 'prompt' is missing.")
		if not A:raise Exception("Warning: 'task_id' is missing.")
		else:
			print(f"RiceRoundOutputImageNode task_id: {A}")
			if C.shape[0]>5:raise ValueError('Error: Cannot upload more than 5 images.')
			G=[]
			for K in C:
				H=machine_upload_image(K,A)
				if not H:raise ValueError('Error: Failed to upload image.')
				G.append(H)
			L={I:_h,'image_results':G};M={_i:A,_M:D,'client_id':E,'prompt_id':F,'timestamp':int(time.time()*1000),I:_h,'result_data':L};PromptServer.instance.send_sync('rice_round_done',M,sid=E)
		return{}
class Encrypt:
	def __init__(A,workflow,prompt,project_name,template_id):
		A.original_workflow=workflow;A.original_prompt=prompt;A.template_id=template_id;A.project_name=project_name;A.project_folder=os.path.join(output_project_folder,A.project_name,A.template_id)
		if not os.path.exists(A.project_folder):os.makedirs(A.project_folder)
		A.output_folder=os.path.join(A.project_folder,'output')
		if not os.path.exists(A.output_folder):os.makedirs(A.output_folder)
		A.publish_folder=os.path.join(A.project_folder,'publish')
		if not os.path.exists(A.publish_folder):os.makedirs(A.publish_folder)
		A.last_node_id=0;A.last_link_id=0;A.link_owner_map=defaultdict(dict);A.workflow_nodes_dict={};A.node_prompt_map={};A.input_node_map={};A.related_node_ids=set()
	def do_encrypt(A):A.load_workflow();A.load_prompt();A.analyze_input_from_workflow();A.assemble_new_workflow();A.output_template_json_file();A.assemble_new_prompt();A.output_file(A.original_workflow,f"original_workflow");A.output_file(A.original_prompt,f"original_prompt");A.save_rice_zip();A.clear();return A.publish_folder
	def clear(A):A.original_workflow=_B;A.original_prompt=_B;A.template_id=_B;A.project_name=_B;A.project_folder=_B;A.last_node_id=0;A.last_link_id=0;RicePromptInfo().clear()
	def load_workflow(A):
		C=copy.deepcopy(A.original_workflow);A.workflow_nodes_dict={int(A[_D]):A for A in C[_F]}
		for F in C[_F]:
			G=F.get(_G,[])
			if not G:continue
			for D in G:
				E=D.get(_C,[])
				if not E:continue
				for B in E:B=int(B);A.link_owner_map[B][_C]=copy.deepcopy(E);A.link_owner_map[B][_j]=D.get(_j,0);A.link_owner_map[B][_u]=int(F[_D]);A.link_owner_map[B][_A]=D.get(_A,'')
		A.last_node_id=int(C[_v]);A.last_link_id=int(C['last_link_id'])
	def load_prompt(A):B=copy.deepcopy(A.original_prompt);A.node_prompt_map={int(A):B for(A,B)in B.items()}
	def analyze_input_from_workflow(A):
		for(id,B)in A.workflow_nodes_dict.items():
			E=B.get(_A,'')
			if E in INPUT_NODE_TYPES:
				A.input_node_map[id]=copy.deepcopy(B);C=B.get(_G,[])
				if not C:continue
				D=C[0].get(_C,[])
				if not D:continue
				F=int(D[0]);A.input_node_map[id][_k]=F;A.input_node_map[id][_w]=C[0].get(_A,_E)
		A.input_node_map={A:B for(A,B)in sorted(A.input_node_map.items(),key=lambda x:x[0])}
	def assemble_new_workflow(A):C=list(A.input_node_map.keys());B=copy.deepcopy(A.original_workflow);A.related_node_ids=A.find_workflow_related_nodes(B[_C],C);B[_F]=[B for B in B[_F]if int(B[_D])in A.related_node_ids];A.invalid_new_workflow(B);D=A.add_decrypt_node(B);A.remove_redundant_links(B);A.remove_unrelated_nodes(B,A.related_node_ids,D);A.replace_choice_template(B);A.replace_workflow_node(B);A.output_file(B,f"{A.template_id}_workflow")
	def output_template_json_file(F):
		S='请上传不超过500KB的图片';P='image/*';O='tip';N='max_size';M='accept';K='number';J='max';I='min';E='settings';C='describe';L=set()
		try:
			from nodes import NODE_DISPLAY_NAME_MAPPINGS as T
			for(U,V)in T.items():L.add(U);L.add(V)
		except ImportError:print('Warning: Could not import NODE_DISPLAY_NAME_MAPPINGS')
		Q=RicePromptInfo();R=[]
		for(G,W)in F.input_node_map.items():
			X=W[_x];B=F.workflow_nodes_dict[G][_A];D=F.node_prompt_map[G].get(_H,{});H=str(D.get(_K,''))
			if not H:H=F.node_prompt_map[G].get(_c,{}).get(_l,'')
			A={_D:str(X),_A:'',C:'输入组件','node_id':str(G),E:{}}
			if B in[_O,_L,_Q]:A[_A]='image_upload';A[C]='请上传图片';A[E]={M:P,N:500000,O:S}
			elif B==_P:A[_A]='mask_image_upload';A[C]='请上传图片并编辑蒙版';A[E]={M:P,N:500000,O:S,'mask':_b}
			elif B in[_R,_S]:A[_A]='mask_upload';A[C]='请上传蒙版';A[E]={M:P,N:50000,O:'请上传不超过50KB的图片'}
			elif B==_n:A[_A]='text';A[C]='提示词';A[E]={'placeholder':'请描述图片内容','multiline':_b}
			elif B==_d or B==_e:A[_A]='choice';A[C]='模型选择';A[E]={'options':Q.get_choice_value(G),_I:D.get(_I,'')};A['addition']=Q.get_choice_node_addition(G)
			elif B==_T or B==_V:A[_A]='number_int';A[C]='数值';A[E]={I:D.get(I,0),J:D.get(J,1000),K:D.get(K,0)}
			elif B==_U or B==_W:A[_A]='number_float';A[C]='数值';A[E]={I:D.get(I,.0),J:D.get(J,1e3),K:D.get(K,.0)}
			elif B==_X or B==_Y:A[_A]='switch';A[C]='开关';A[E]={_I:D.get('value',False)}
			else:raise ValueError(f"Error: The node {G} is not a valid RiceRound node.")
			if H and H not in L:A[C]=H
			R.append(A)
		Y={_f:F.template_id,'elements':R};F.output_file(Y,f"{F.template_id}_template")
	def assemble_new_prompt(A):'\n        组装新的prompt配置。主要完成:\n        1. 移除不需要的节点\n        2. 转换特定节点的类型和输入\n        3. 保存处理后的prompt配置\n        ';B=A._create_filtered_prompt();A._replace_encrypt_node(B);A._transform_node_types(B);A.output_file(B,f"{A.template_id}_job")
	def _create_filtered_prompt(B):
		'\n        创建经过过滤的prompt副本，移除不需要的节点\n        ';A=copy.deepcopy(B.original_prompt);C=B._get_exclude_node_ids(A)
		for D in C:A.pop(str(D),_B)
		return A
	def _replace_encrypt_node(D,new_prompt):
		C='RiceRoundOutputImageNode'
		for(E,A)in new_prompt.items():
			B=A.get(_N,'');print(f"class_type: {B}")
			if B=='RiceRoundEncryptNode':
				A[_N]=C;A[_H][_i]='';A[_H].pop(_q,_B)
				if _c in A and _l in A[_c]:A[_c][_l]=C
	def save_rice_zip(A):
		import pyzipper as B
		try:
			C=[]
			for(E,F)in enumerate([f"{A.template_id}_job.json",f"{A.template_id}_template.json",f"{A.template_id}_workflow.json",'original_workflow.json','original_prompt.json']):G=os.path.join(A.output_folder,F);C.append((G,f"{E}.bin"))
			H=os.path.join(A.publish_folder,f"{A.template_id}.bin")
			with B.AESZipFile(H,'w',compression=B.ZIP_DEFLATED,encryption=B.WZ_AES)as D:
				D.setpassword(A.template_id.encode())
				for(I,J)in C:D.write(I,J)
			shutil.copy2(os.path.join(A.output_folder,f"{A.template_id}_template.json"),os.path.join(A.publish_folder,'template.json'));shutil.copy2(os.path.join(A.output_folder,f"{A.template_id}_workflow.json"),os.path.join(A.project_folder,'workflow.json'))
		except Exception as K:print(f"Error creating zip: {str(K)}");raise
	def _get_exclude_node_ids(A,prompt):
		'\n        获取需要从prompt中排除的节点ID集合\n        ';C={_m};B=A.related_node_ids.difference(set(A.input_node_map.keys()))
		for(D,E)in prompt.items():
			if E.get(_N,'')in C:B.add(int(D))
		return B
	def _transform_node_types(K,prompt):
		'\n        转换节点类型和更新节点输入配置\n        ';E='str';D='image_url';B='new_inputs';A='new_type';F={_Q:{A:_L,B:{D:''}},_O:{A:_L,B:{D:''}},_P:{A:'RiceRoundDownloadImageAndMaskNode',B:{D:''}},_R:{A:_S,B:{'mask_url':''}},_T:{A:_V,B:{E:''}},_U:{A:_W,B:{E:''}},_X:{A:_Y,B:{E:''}}}
		for(L,C)in prompt.items():
			C.pop('is_changed',_B);G=C.get(_N,'');H=C.get(_H,{})
			if not H:continue
			I=H.get(_K,'')
			if G in F:
				J=F[G];C[_N]=J[A];C[_H]=J[B].copy()
				if I:C[_H][_K]=I
	def add_decrypt_node(A,workflow):
		K='label';C=workflow;G=set();A.last_node_id+=1;H={_D:A.last_node_id,_A:_m,'pos':[420,0],'size':[500,150],'flags':{},'mode':0,'order':20,_H:[],_G:[{_K:_J,_A:_J,_C:[],K:_J,_j:0}],_y:{_z:_m},'widgets_values':[str(A.template_id),735127949069071,'randomize']}
		for(B,(D,E))in enumerate(A.input_node_map.items()):
			I=E[_k];F=E[_w];E[_x]=B;J={_K:f"input_anything{B if B>0 else''} ({D})",_A:'*','link':I,K:f"input_anything{B if B>0 else''} ({D})"}
			if B==0:J['shape']=7
			H[_H].append(J)
			if F not in[_J,_E]:F=_E
			L=[I,D,0,A.last_node_id,B,F];C[_C].append(L)
		G.add(A.last_node_id);C[_F].append(H);C[_v]=A.last_node_id;return G
	def output_file(A,workflow,prefix):
		B=os.path.join(A.output_folder,f"{prefix}.json")
		with open(B,'w',encoding='utf-8')as C:json.dump(workflow,C,ensure_ascii=False,indent=4)
	def remove_redundant_links(C,workflow):
		A=workflow;D=set()
		for E in A[_F]:
			F=int(E[_D])
			if F in C.input_node_map:
				G=C.input_node_map[F][_k];B=E.get(_G,[])
				if not B:continue
				for J in B:
					H=J.get(_C,[])
					if not H:continue
					for I in H:
						if I!=G:D.add(I)
				B[0][_C]=[G]
		A[_C]=[A for A in A[_C]if isinstance(A,list)and len(A)==6 and A[0]not in D]
	def replace_choice_template(H,workflow):
		D='extra';C=workflow;E=RicePromptInfo()
		for A in C[_F]:
			B=int(A[_D])
			if A.get(_A,'')==_e:
				F=E.get_choice_classname(B)
				if F:A[_A]=F
				else:print(f"Warning: The node {B} is not a valid RiceRound Choice node.")
		G={}
		for(B,A)in H.input_node_map.items():
			if A.get(_A,'')==_d:I=E.get_choice_value(B);G[B]=I
		if D not in C:C[D]={}
		C[D]['choice_node_map']=G
	def replace_workflow_node(L,workflow):
		K='unknown';J='RiceRoundUploadImageNode';F=workflow;E='RiceRoundOutputTextNode';B={_Q:('RiceRoundOutputImageBridgeNode',''),_O:(J,''),_P:(J,'Image&Mask'),_L:('RiceRoundImageUrlNode',''),_R:('RiceRoundOutputMaskBridgeNode',''),_S:('RiceRoundMaskUrlNode',''),_T:('RiceRoundOutputIntNode',''),_U:('RiceRoundOutputFloatNode',''),_X:('RiceRoundOutputBooleanNode',''),_Y:(E,''),_V:(E,''),_W:(E,'')};G=set()
		for A in F[_F]:
			C=A.get(_A,'')
			if C in B:
				if _G not in A:raise ValueError(f"Node {A.get(_D,K)} missing outputs")
				if not A[_G]or not isinstance(A[_G],list):raise ValueError(f"Invalid outputs format in node {A.get(_D,K)}")
				H=B[C][0];I=H if B[C][1]==''else B[C][1];A.update({_K:I,_A:H,_G:[{_A:_E,**A[_G][0]}],_y:{_z:I}});G.add(int(A[_D]))
		for D in F[_C]:
			if len(D)==6 and D[1]in G:D[5]=_E
	def remove_unrelated_nodes(E,workflow,related_node_ids,new_node_ids):
		B=workflow;C=[];D=related_node_ids.union(new_node_ids)
		for A in B[_C]:
			if len(A)==6:
				if A[1]in D and A[3]in D:C.append(A)
		B[_C]=C
	def invalid_new_workflow(A,workflow):
		for B in workflow[_F]:
			C=B.get(_H,[])
			for input in C:
				D=int(input.get('link',0));E=A.link_owner_map[D][_u];F=A.workflow_nodes_dict[E][_A]
				if F in INPUT_NODE_TYPES:raise ValueError(f"Error: The node {B[_D]} may have circular references, generation failed.")
	def find_workflow_related_nodes(F,links,input_ids):
		E=input_ids;B=set(E);C=list(E)
		while C:
			G=C.pop()
			for D in links:
				if len(D)==6 and D[3]==G:
					A=D[1]
					if A not in B:
						if A in F.workflow_nodes_dict:B.add(A)
					C.append(A)
		return B