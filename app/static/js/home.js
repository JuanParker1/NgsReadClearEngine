// const dropzone = new Dropzone("div.my-dropzone", { url: "/" });

// const buttonClick = () => {
//     const job_form = document.getElementById("job_form")
//     const job_button = document.getElementById("job_button")

//     job_button.classList.remove('opacity-100');
//     job_button.classList.add('opacity-0');
//     job_button.classList.add('hidden');

//     job_form.classList.remove("invisible");
//     job_form.classList.remove("absolute", "bottom-0", "left-0");
//     job_form.classList.add('opacity-100');
//   }

//   const file_input = document.getElementById("file_input");
//   const checkMail = (event) => {
//     const res = String(event.target.value).toLowerCase().match(
//       /^(([^<>()[\]\\.,;:\s@"]+(\.[^<>()[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/
//     );
//     const button_label = document.getElementById("button_label");

//     if (res == null) {
//       event.target.classList.remove("text-green-600");
//       event.target.classList.add("text-red-500");
//       event.target.valid = false;
//       button_label.classList.remove("hover:bg-green-600","hover:text-white", "text-green-600", "cursor-pointer")
//       button_label.classList.add("bg-gray-600","text-white")
//       file_input.disabled = true;

//     } else {
//       event.target.classList.remove("text-red-500");
//       event.target.classList.add("text-green-600");
//       event.target.valid = true;
//       button_label.classList.remove("bg-gray-600","text-white")
//       button_label.classList.add("hover:bg-green-600","hover:text-white", "text-green-600", "cursor-pointer")
//       file_input.disabled = false;
//     }

//   }

//   const email = document.getElementById("email");
//   email.value = ""
//   email.addEventListener('input', checkMail);

 
//   const validateInput = (event) => {
   
//     if (event.target.form[0].valid) {
//         const job_form = document.getElementById("job_form")
//         const after_post = document.getElementById("after_post")

//         job_form.classList = ['hidden'];
//         after_post.classList.remove("hidden")
//         postFile()

//     }
//   }


//   function postFile() {
//     let formdata = new FormData();

//     formdata.append('file', document.getElementById("file_input").files[0]);
//     formdata.append('email', document.getElementById("email").value);

//     let request = new XMLHttpRequest();

//     request.upload.addEventListener('progress', (event) => {

//       var file1Size = document.getElementById('file_input').files[0].size;
//         if (event.loaded <= file1Size) {
//           var percent = Math.round(event.loaded / file1Size * 100);
//         //   document.getElementById('progress-bar').style.width = percent + '%';
//           document.getElementById('progress-bar').innerHTML = percent + '%';
//         }
//         if(event.loaded == event.total){
//         //   document.getElementById('progress-bar').style.width = '100%';
//           document.getElementById('progress-bar').innerHTML = '100%';
//         }
//     });
   

//     request.open('POST', '');
//     request.timeout = 45000;
//     request.send(formdata);

//     request.onreadystatechange = () => {
//         if (request.readyState == XMLHttpRequest.DONE) {
//             var OK = 200;

//             if (request.status === OK) {
//                 window.location.href = request.responseURL;
//             }
//             else {
//                 console.log ('Error: ' + request.status);
//             }
//         }
//     };

// }

// const cancelPost = () => {
//   console.log("cancel request")
// }

// file_input.addEventListener('change', validateInput);


//var dropzone = new Dropzone('#dropper', {

//  parallelUploads: 2,
//  thumbnailHeight: 120,
//  thumbnailWidth: 120,
//  maxFilesize: 1000,
//  filesizeBase: 1000,
//  thumbnail: function(file, dataUrl) {
//    if (file.previewElement) {
//      file.previewElement.classList.remove("dz-file-preview");
//      var images = file.previewElement.querySelectorAll("[data-dz-thumbnail]");
//      for (var i = 0; i < images.length; i++) {
//        var thumbnailElement = images[i];
//        thumbnailElement.alt = file.name;
//        thumbnailElement.src = dataUrl;
//      }
//      setTimeout(function() { file.previewElement.classList.add("dz-image-preview"); }, 1);
//    }
//  }
//
//});


// Now fake the file upload, since GitHub does not handle file uploads
// and returns a 404

var minSteps = 6,
    maxSteps = 60,
    timeBetweenSteps = 100,
    bytesPerStep = 100000;

Dropzone.options.dropper = {
    paramName: 'file',
    chunking: true,
    forceChunking: true,
    url: '/',
    maxFilesize: 4096, // MegaBytes
    chunkSize: 1000000, // bytes
    init: function () {
      this.on("complete", function (file) {
        window.location = "{{ url_for('/') }}";
      });
    }
}
