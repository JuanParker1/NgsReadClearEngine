const job_form = document.getElementById("theForm")
const buttonClick = () => {
  const form_div = document.getElementById("formdiv")
  const job_button = document.getElementById("job_button")

  job_button.classList.remove('opacity-100');
  job_button.classList.add('opacity-0');
  job_button.classList.add('hidden');

  form_div.classList.remove("invisible");
  form_div.classList.remove("absolute", "bottom-0", "left-0");
  form_div.classList.add('opacity-100');
}


  const theFile = document.getElementById("theFile");
  const checkMail = (event) => {
    const res = String(event.target.value).toLowerCase().match(
      /^(([^<>()[\]\\.,;:\s@"]+(\.[^<>()[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/
    );
    const continue_button = document.getElementById("continue_after_mail");
    
    if (res == null) {
      event.target.classList.remove("text-green-600");
      event.target.classList.add("text-red-500");
      event.target.valid = false;
      continue_button.classList.remove("hover:bg-green-600","hover:text-white", "text-green-600", "cursor-pointer")
      continue_button.classList.add("bg-gray-600","text-white")
      theFile.disabled = true;
      continue_button.removeEventListener("click", formForward)

    } else {
      event.target.classList.remove("text-red-500");
      event.target.classList.add("text-green-600");
      event.target.valid = true;
      continue_button.classList.remove("bg-gray-600","text-white")
      continue_button.classList.add("hover:bg-green-600","hover:text-white", "text-green-600", "cursor-pointer")
      theFile.disabled = false;
      continue_button.addEventListener("click", formForward)
    }

  }

  const email = document.getElementById("theMail");
  email.value = ""
  email.addEventListener('input', checkMail);

  const formForward = () => {
    if (job_form[0].value) {
      document.getElementById("mail_div").classList.add("hidden");
      document.getElementById("file_div").classList.remove("hidden");
    }
    if (job_form[1].value) {
      document.getElementById("file_div").classList.add("hidden");
      document.getElementById("database_div").classList.remove("hidden");
    }
    console.log(job_form)

  }


  // const formBack = () => {
  //   job_form
  // }
  
  const validateInput = (event) => {
    if (event.target.form[0].valid) {
        const job_form = document.getElementById("theForm")
        const after_post = document.getElementById("after_post")

        job_form.classList = ['hidden'];
        after_post.classList.remove("hidden")
        postForm()
    }
  }






  function postForm() {
    let formdata = new FormData();

    formdata.append('file', document.getElementById("theFile").files[0]);
    formdata.append('email', document.getElementById("theMail").value);

    let request = new XMLHttpRequest();

    request.upload.addEventListener('progress', (event) => {

      var file1Size = document.getElementById('theFile').files[0].size;
        if (event.loaded <= file1Size) {
          var percent = Math.round(event.loaded / file1Size * 100);
        //   document.getElementById('progress-bar').style.width = percent + '%';
          document.getElementById('progress-bar').innerHTML = percent + '%';
        }
        if(event.loaded == event.total){
        //   document.getElementById('progress-bar').style.width = '100%';
          document.getElementById('progress-bar').innerHTML = '100%';
        }
    });
    

    request.open('POST', '');
    request.send(formdata);

    request.onreadystatechange = () => {
        if (request.readyState == XMLHttpRequest.DONE) {
            var OK = 200;

            if (request.status === OK) {
                window.location.href = request.responseURL;
            }
            else {
                console.log ('Error: ' + request.status); 
            }
        }
    };

}


theFile.addEventListener('change', formForward);
theFile.value = null