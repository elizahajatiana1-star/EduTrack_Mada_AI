
// Afficher / cacher le mot de passe

const password = document.getElementById("password");

const showPassword = document.getElementById("showPassword");


showPassword.addEventListener("click",()=>{


    if(password.type === "password"){

        password.type="text";

        showPassword.textContent="🙈";

    }

    else{

        password.type="password";

        showPassword.textContent="👁";

    }


});




// Simulation connexion

const form = document.getElementById("loginForm");


form.addEventListener("submit",(e)=>{


    e.preventDefault();


    alert(
        "Connexion réussie à EduTrack Madagascar AI 🎓"
    );


});
