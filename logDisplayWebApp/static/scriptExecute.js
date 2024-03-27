/**
 *
 * Copyright (c) 2023 Project CHIP Authors
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
function start_script(script_name, script_path) {
  
  var arguments = document.getElementById(script_name).value;
  
  
  if (arguments.length>0){
  arguments.replaceAll(" ",":")
  console.log(arguments)
  var data = { script_name: script_name, script_path: script_path, arguments: arguments }
  fetch("/execute_script", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(data)
  })
  .then(function(response){
    if (response.status=200){
      return response.json()
    }
    else {
      alert("server returned status code"+response.status)
    }
  })
  .then(function(data){
      alert(data["message"])
   
  })
  }
  else{
    alert("Arguments filed is empty")
  }
  
}

function showStatus(script_name,script_details){
console.log(script_details)
alert(script_details[script_name]);
}