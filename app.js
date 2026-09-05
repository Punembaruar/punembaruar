const $=(s,r=document)=>r.querySelector(s), $$=(s,r=document)=>[...r.querySelectorAll(s)];
function toast(msg){const t=$('#toast');if(!t)return; t.textContent=msg;t.classList.add('show');setTimeout(()=>t.classList.remove('show'),2600)}
$$('[data-scroll]').forEach(b=>b.onclick=()=>$('#'+b.dataset.scroll)?.scrollIntoView({behavior:'smooth'}));
$$('.chip').forEach(c=>c.onclick=()=>c.classList.toggle('active'));
async function postJSON(url,data){const r=await fetch(url,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});const j=await r.json();if(!r.ok)throw new Error(j.detail||'Gabim');return j}
const rf=$('#requestForm');if(rf)rf.addEventListener('submit',async e=>{e.preventDefault();try{const data={name:$('#name').value,phone:$('#phone').value,category_slug:$('#categorySlug').value,request_type:$('#categorySlug').selectedOptions[0].text,description:$('#description').value,city:$('#city').value,zone:$('#zone').value||null,vehicle_make:$('#make').value||null,vehicle_model:$('#model').value||null,vehicle_year:$('#year').value||null,vehicle_engine:$('#engine').value||null,vehicle_fuel:$('#fuel')?.value||null,urgency:$('#urgency')?.value||null,preferred_timing:$('#urgency')?.value||null,source:new URLSearchParams(location.search).get('utm_source')||'direct'};const j=await postJSON('/api/requests',data);const box=$('#requestResult');box.classList.remove('hidden');box.innerHTML=`<strong>Kërkesa #Kërkesa juaj iu dërgua profesionistëve të përshtatshëm. Do të merrni ofertat sapo profesionistët të përgjigjen.`;toast('Kërkesa u publikua');}catch(err){toast(err.message)}});
const pf=$('#professionalForm');if(pf)pf.addEventListener('submit',async e=>{e.preventDefault();try{const cats=$$('#proCats .chip.active').map(x=>x.dataset.slug);const data={name:$('#proName').value,phone:$('#proWhatsApp').value,whatsapp:$('#proWhatsApp').value,professional_type:$('#proType').value,city:$('#proCity').value,zone:$('#proZone').value||null,category_slugs:cats};const j=await postJSON('/api/professionals',data);const box=$('#proResult');box.classList.remove('hidden');box.innerHTML=`<strong>U regjistrua.</strong> ID profesionisti: ${j.professional_id}. Founding Member: ${j.founding_member?'Po':'Jo'}`;toast('Profili u krijua');}catch(err){toast(err.message)}});
const of=$('#offerForm');if(of)of.addEventListener('submit',async e=>{e.preventDefault();try{const req=Number(of.dataset.request),pro=Number(of.dataset.professional);const qt=$('#quoteType')?.value||'fixed';const price=$('#offerPrice')?.value?Number($('#offerPrice').value):null;const j=await postJSON(`/api/requests/${req}/offers`,{professional_id:pro,quote_type:qt,price:qt==='fixed'?price:null,price_from:$('#offerFrom')?.value?Number($('#offerFrom').value):null,price_to:$('#offerTo')?.value?Number($('#offerTo').value):null,diagnostic_fee:$('#diagnosticFee')?.value?Number($('#diagnosticFee').value):null,parts_price:$('#partsPrice')?.value?Number($('#partsPrice').value):null,labor_price:$('#laborPrice')?.value?Number($('#laborPrice').value):null,estimated_time:$('#estimatedTime')?.value||null,warranty:$('#offerWarranty')?.value||null,appointment_note:$('#appointmentNote')?.value||null,message:$('#offerMessage').value||null});const box=$('#offerResult');box.classList.remove('hidden');box.innerHTML=`<strong>Oferta #${j.offer_id} u dërgua.</strong>`;}catch(err){const box=$('#offerResult');box.classList.remove('hidden');box.textContent=err.message}});

const loginForm=$('#loginForm');
if(loginForm){
  $('#sendOtp')?.addEventListener('click',async()=>{
    try{
      const j=await postJSON('/api/auth/otp/start',{phone:$('#loginPhone').value});
      $('#otpArea').classList.remove('hidden');
      $('#devOtp').innerHTML=`<strong>Kodi DEV:</strong> ${j.dev_code}<br><small>Në production ky kod do të vijë me SMS.</small>`;
      $('#loginCode').value=j.dev_code;
      toast('Kodi OTP u krijua');
    }catch(err){toast(err.message)}
  });
  loginForm.addEventListener('submit',async e=>{
    e.preventDefault();
    try{
      const j=await postJSON('/api/auth/session',{phone:$('#loginPhone').value,code:$('#loginCode').value,name:$('#loginName').value||'Klient'});
      location.href=j.dashboard_url;
    }catch(err){toast(err.message)}
  });
}

$$('.logoutBtn').forEach(b=>b.addEventListener('click',async()=>{try{await postJSON('/api/auth/logout',{});location.href='/'}catch(e){location.href='/'}}));

$$('.acceptOffer').forEach(b=>b.addEventListener('click',async()=>{
  try{const j=await postJSON(`/api/offers/${b.dataset.offer}/accept`,{});toast('Oferta u pranua');setTimeout(()=>location.reload(),500)}catch(err){toast(err.message)}
}));

const mf=$('#messageForm');if(mf)mf.addEventListener('submit',async e=>{
  e.preventDefault(); try{await postJSON(`/api/requests/${mf.dataset.request}/messages`,{body:$('#messageBody').value});$('#messageBody').value='';location.reload()}catch(err){toast(err.message)}
});

$$('.completeRequest').forEach(b=>b.addEventListener('click',async()=>{
  try{await postJSON(`/api/requests/${b.dataset.request}/complete`,{});toast('Puna u shënua e përfunduar');setTimeout(()=>location.reload(),500)}catch(err){toast(err.message)}
}));

const rev=$('#reviewForm');if(rev)rev.addEventListener('submit',async e=>{
  e.preventDefault();try{await postJSON(`/api/requests/${rev.dataset.request}/review`,{rating:Number($('#reviewRating').value),comment:$('#reviewComment').value||null});toast('Review u ruajt');setTimeout(()=>location.reload(),500)}catch(err){toast(err.message)}
});
$$('.verifyPro').forEach(b=>b.addEventListener('click',async()=>{try{await postJSON(`/api/admin/professionals/${b.dataset.id}/verify`,{});location.reload()}catch(err){toast(err.message)}}));
$$('.markSent').forEach(b=>b.addEventListener('click',async()=>{try{await postJSON(`/api/admin/notifications/${b.dataset.id}/mark-sent`,{});location.reload()}catch(err){toast(err.message)}}));
const cf=$('#categoryForm');if(cf)cf.addEventListener('submit',async e=>{e.preventDefault();try{await postJSON('/api/admin/categories',{name:$('#newCatName').value,slug:$('#newCatSlug').value,parent_slug:$('#newCatParent').value});toast('Kategoria u shtua');setTimeout(()=>location.reload(),400)}catch(err){toast(err.message)}});

// V1.0: Garage + media uploads
const gf=$('#garageForm');if(gf)gf.addEventListener('submit',async e=>{e.preventDefault();try{await postJSON('/api/garage',{make:$('#gMake').value,model:$('#gModel').value,year:$('#gYear').value||null,engine:$('#gEngine').value||null,fuel:$('#gFuel').value||null});toast('Automjeti u shtua');setTimeout(()=>location.reload(),400)}catch(err){toast(err.message)}});
$$('.deleteVehicle').forEach(b=>b.addEventListener('click',async()=>{try{const r=await fetch(`/api/garage/${b.dataset.id}`,{method:'DELETE'});const j=await r.json();if(!r.ok)throw new Error(j.detail||'Gabim');location.reload()}catch(err){toast(err.message)}}));
async function uploadFile(url,file){const fd=new FormData();fd.append('file',file);const r=await fetch(url,{method:'POST',body:fd});const j=await r.json();if(!r.ok)throw new Error(j.detail||'Gabim upload');return j}
const rmf=$('#requestMediaForm');if(rmf)rmf.addEventListener('submit',async e=>{e.preventDefault();try{await uploadFile(`/api/requests/${rmf.dataset.request}/media`,$('#requestMediaFile').files[0]);toast('Media u ngarkua');setTimeout(()=>location.reload(),400)}catch(err){toast(err.message)}});
const pmf=$('#proMediaForm');if(pmf)pmf.addEventListener('submit',async e=>{e.preventDefault();try{await uploadFile(`/api/professionals/${pmf.dataset.professional}/media`,$('#proMediaFile').files[0]);toast('Foto u ngarkua');setTimeout(()=>location.reload(),400)}catch(err){toast(err.message)}});

// V1.1: low-cost admin controls
const sf=$('#settingsForm');if(sf)sf.addEventListener('submit',async e=>{e.preventDefault();try{await postJSON('/api/admin/settings',{matching_batch_size:Number($('#matchingBatch').value),matching_max_professionals:Number($('#matchingMax').value),matching_same_city_required:$('#sameCity').checked,whatsapp_enabled:$('#waEnabled').checked});toast('Konfigurimi u ruajt')}catch(err){toast(err.message)}});
$$('.proPlan').forEach(s=>s.addEventListener('change',async()=>{try{await postJSON(`/api/admin/professionals/${s.dataset.id}/update`,{plan:s.value});toast('Plani u ndryshua')}catch(err){toast(err.message)}}));
$$('.togglePro').forEach(b=>b.addEventListener('click',async()=>{try{const active=b.dataset.active!=='true';await postJSON(`/api/admin/professionals/${b.dataset.id}/update`,{active});location.reload()}catch(err){toast(err.message)}}));

$$('.auto-choice').forEach(b=>b.addEventListener('click',()=>{const sel=$('#categorySlug');if(sel){sel.value=b.dataset.slug;$('#request')?.scrollIntoView({behavior:'smooth'});}}));
const qt=$('#quoteType');function toggleQuote(){if(!qt)return;$('#fixedQuote')?.classList.toggle('hidden',qt.value!=='fixed');$('#rangeQuote')?.classList.toggle('hidden',qt.value!=='range');$('#diagnosticQuote')?.classList.toggle('hidden',qt.value!=='diagnostic')}if(qt){qt.addEventListener('change',toggleQuote);toggleQuote()}

function togglePartsSpecific(){
 const s=$('#categorySlug'); const box=$('#partsSpecific');
 if(s&&box) box.classList.toggle('hidden', s.value!=='pjese-kembimi');
}
$('#categorySlug')?.addEventListener('change',togglePartsSpecific); togglePartsSpecific();
