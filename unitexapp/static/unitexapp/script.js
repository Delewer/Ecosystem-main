// Smooth scroll for navigation links with active link highlight
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        document.querySelector(this.getAttribute('href')).scrollIntoView({
            behavior: 'smooth'
        });

        // Add active class to the clicked link
        document.querySelectorAll('.nav-link').forEach(link => {
            link.classList.remove('active');
        });
        this.classList.add('active');
    });
});

// Animate shapes in welcome section with more effects
const shapes = document.querySelectorAll('.shape');
shapes.forEach(shape => {
    let randomX = 0;
    let randomY = 0;
    let randomRotation = 0;
    let randomScale = 1;
    let interval = Math.random() * 3000 + 1500;

    setInterval(() => {
        randomX = Math.random() * 30 - 15;
        randomY = Math.random() * 30 - 15;
        randomRotation = Math.random() * 360;
        randomScale = 0.9 + Math.random() * 0.2;

        shape.style.transition = 'transform 1s ease-out, filter 1s ease-out';
        shape.style.transform = `translate(${randomX}px, ${randomY}px) rotate(${randomRotation}deg) scale(${randomScale})`;
        shape.style.filter = `blur(${Math.random() * 2}px) brightness(${0.8 + Math.random() * 0.4})`;
    }, interval);
});

// Animate features on scroll with staggered delays
const features = document.querySelectorAll('.feature');
const animateFeatures = () => {
    features.forEach((feature, index) => {
        const featureTop = feature.getBoundingClientRect().top;
        const windowHeight = window.innerHeight;

        if (featureTop < windowHeight * 0.75) {
            feature.style.opacity = '1';
            feature.style.transform = 'translateY(0)';
            feature.style.transition = `all 0.6s ease-out ${index * 0.2}s`; // Staggered animation
        }
    });
};

features.forEach(feature => {
    feature.style.opacity = '0';
    feature.style.transform = 'translateY(50px)';
});

window.addEventListener('scroll', animateFeatures);

// Находим все карточки программ
const programCards = document.querySelectorAll('.program-card');

// Добавляем обработчик для каждой карточки
programCards.forEach(card => {
    // Создаем элемент для дополнительной информации
    const expandedInfo = document.createElement('div');
    expandedInfo.className = 'expanded-info';
    
    // Получаем название программы из текущей карточки
    const programTitle = card.querySelector('.program-title').textContent;
    
    // Объект с дополнительной информацией для каждой программы
    const programDetails = {
        'Programare de bază': {
            description: 'Un curs captivant de introducere în programare folosind Python, special conceput pentru copiii cu vârste între 7 și 9 ani.',
            duration: '3 luni',
            schedule: '2 ore pe săptămână',
            skills: ['Gândire algoritmică', 'Bazele programării', 'Rezolvarea problemelor', 'Lucrul cu variabile și funcții simple'],
            projects: ['Jocuri simple', 'Calculatoare interactive', 'Povești animate'],
        },
        'Programare avansată': {
            description: 'Curs avansat de Java pentru tinerii pasionați de programare, cu focus pe dezvoltarea aplicațiilor practice.',
            duration: '4 luni',
            schedule: '3 ore pe săptămână',
            skills: ['Programare orientată pe obiecte', 'Structuri de date', 'Algoritmi', 'Design patterns'],
            projects: ['Aplicații desktop', 'Jocuri complexe', 'Sisteme de management'],
        },
        'Dezvoltare web': {
            description: 'Învață să creezi site-uri web moderne și interactive folosind cele mai recente tehnologii web.',
            duration: '4 luni',
            schedule: '3 ore pe săptămână',
            skills: ['HTML5', 'CSS3', 'JavaScript', 'Responsive Design'],
            projects: ['Portfolio personal', 'Blog', 'E-commerce site'],
        },
        'Aplicații mobile': {
            description: 'Dezvoltă aplicații mobile native pentru Android și iOS folosind tehnologii moderne.',
            duration: '5 luni',
            schedule: '4 ore pe săptămână',
            skills: ['Mobile UI/UX', 'Native APIs', 'Data Storage', 'App Publishing'],
            projects: ['Social Media App', 'Game App', 'Utility App'],
        },
        'Robotica cu Arduino': {
            description: 'Explorează lumea fascinantă a roboticii prin proiecte practice cu Arduino.',
            duration: '3 luni',
            schedule: '3 ore pe săptămână',
            skills: ['Electronică de bază', 'Programare C++', 'Design 3D', 'Senzori și actuatori'],
            projects: ['Robot urmăritor', 'Sistem de irigație automatizat', 'Stație meteo'],
            price: '400 RON/lună'
        },
        'Programare vizuală': {
            description: 'Învață programarea într-un mod distractiv și interactiv folosind Scratch.',
            duration: '2 luni',
            schedule: '2 ore pe săptămână',
            skills: ['Logică de programare', 'Animații', 'Storytelling', 'Game Design'],
            projects: ['Jocuri interactive', 'Animații', 'Povești digitale'],
        },
        'Introducere în AI': {
            description: 'Descoperă bazele inteligenței artificiale și aplicațiile sale în lumea modernă.',
            duration: '4 luni',
            schedule: '3 ore pe săptămână',
            skills: ['Machine Learning', 'Neural Networks', 'Data Analysis', 'Python pentru AI'],
            projects: ['Chatbot', 'Image Recognition', 'Predictive Models'],
        },
        'Modelarea 3D': {
            description: 'Învață să creezi modele și animații 3D folosind software profesional.',
            duration: '3 luni',
            schedule: '3 ore pe săptămână',
            skills: ['3D Modeling', 'Texturing', 'Animation', 'Rendering'],
            projects: ['Character Design', 'Product Visualization', 'Architectural Models'],

        }
    };

    // Получаем детали для конкретной программы
    const details = programDetails[programTitle];
    
    // Создаем HTML для дополнительной информации
    expandedInfo.innerHTML = `
        <p class="expanded-description">${details.description}</p>
        <div class="program-details">
            <div class="detail-item">
                <strong>Durată:</strong> ${details.duration}
            </div>
            <div class="detail-item">
                <strong>Program:</strong> ${details.schedule}
            </div>
        </div>
        <div class="skills-section">
            <strong>Competențe dobândite:</strong>
            <ul>
                ${details.skills.map(skill => `<li>${skill}</li>`).join('')}
            </ul>
        </div>
        <div class="projects-section">
            <strong>Proiecte:</strong>
            <ul>
                ${details.projects.map(project => `<li>${project}</li>`).join('')}
            </ul>
        </div>
        <button class="enroll-button">Înscrie-te acum</button>
    `;
    
    // Добавляем дополнительную информацию в карточку
    card.appendChild(expandedInfo);
    
    // Добавляем обработчик клика
    card.addEventListener('click', () => {
        // Закрываем все другие открытые карточки
        programCards.forEach(otherCard => {
            if (otherCard !== card && otherCard.classList.contains('expanded')) {
                otherCard.classList.remove('expanded');
                otherCard.querySelector('.expanded-info').style.maxHeight = '0';
            }
        });
        
        // Переключаем состояние текущей карточки
        card.classList.toggle('expanded');
        const info = card.querySelector('.expanded-info');
        
        if (card.classList.contains('expanded')) {
            info.style.maxHeight = info.scrollHeight + 'px';
        } else {
            info.style.maxHeight = '0';
        }
    });
});

// Предотвращаем всплытие события для кнопки записи
document.querySelectorAll('.enroll-button').forEach(button => {
    button.addEventListener('click', (e) => {
        e.stopPropagation();
        // Здесь можно добавить логику для записи на курс
        alert('Vă mulțumim pentru interes! În curând vă vom contacta pentru înscriere.');
    });
});

// Add typing effect to welcome section heading with an animation for each letter
const welcomeHeading = document.querySelector('.welcome-content h1');
const originalText = welcomeHeading.textContent;
welcomeHeading.textContent = '';

const typeText = async () => {
    for (let i = 0; i < originalText.length; i++) {
        welcomeHeading.textContent += originalText[i];
        welcomeHeading.style.transition = 'color 0.3s ease-out';
        welcomeHeading.style.color = '#4CAF50'; // Adding color change effect to text
        await new Promise(resolve => setTimeout(resolve, 50)); 
    }
};

document.addEventListener('DOMContentLoaded', typeText);

// Form validation with smooth focus/blur effects
const form = document.querySelector('.signup-section form');
const inputs = form.querySelectorAll('input');

inputs.forEach(input => {
    input.addEventListener('focus', () => {
        input.parentElement.style.transform = 'scale(1.05)';
        input.style.borderColor = '#4CAF50';
        input.style.transition = 'transform 0.3s ease, border-color 0.3s ease';
    });

    input.addEventListener('blur', () => {
        input.parentElement.style.transform = 'scale(1)';
        input.style.borderColor = '#ddd';
    });
});

form.addEventListener('submit', (e) => {
    e.preventDefault();
    let isValid = true;
    
    inputs.forEach(input => {
        if (!input.value) {
            isValid = false;
            input.style.borderColor = '#ff0000';
            input.classList.add('shake');
            setTimeout(() => input.classList.remove('shake'), 500);
        }
    });
    
    if (isValid) {
        const button = form.querySelector('button');
        button.textContent = 'Se trimite...';
        button.disabled = true;
        
        setTimeout(() => {
            button.textContent = 'Trimis cu succes!';
            button.style.backgroundColor = '#45a049';
            button.style.transition = 'background-color 0.3s ease';
            
            setTimeout(() => {
                form.reset();
                button.textContent = 'Trimite';
                button.disabled = false;
                button.style.backgroundColor = '#4CAF50';
            }, 2000);
        }, 1500);
    }
});

// Scroll progress indicator with smooth transition
const progressBar = document.createElement('div');
progressBar.className = 'scroll-progress';
progressBar.style.height = '5px';
progressBar.style.backgroundColor = '#4CAF50';
progressBar.style.position = 'fixed';
progressBar.style.top = '0';
progressBar.style.left = '0';
progressBar.style.transition = 'width 0.3s ease-out';
document.body.appendChild(progressBar);

window.addEventListener('scroll', () => {
    const windowHeight = document.documentElement.scrollHeight - window.innerHeight;
    const scrolled = (window.pageYOffset / windowHeight) * 100;
    progressBar.style.width = `${scrolled}%`;
});

// Create a modern floating scroll to top button
const scrollTopButton = document.createElement('button');
scrollTopButton.className = 'scroll-top-button';
scrollTopButton.innerHTML = '↑';  // Using Font Awesome icon
scrollTopButton.style.position = 'fixed';
scrollTopButton.style.bottom = '30px';
scrollTopButton.style.right = '30px';
scrollTopButton.style.backgroundColor = '#4CAF50';
scrollTopButton.style.color = '#fff';
scrollTopButton.style.border = 'none';
scrollTopButton.style.borderRadius = '50%';
scrollTopButton.style.width = '60px'; // Increased size for better accessibility
scrollTopButton.style.height = '60px';
scrollTopButton.style.fontSize = '24px'; // Slightly smaller icon
scrollTopButton.style.display = 'flex';
scrollTopButton.style.alignItems = 'center';
scrollTopButton.style.justifyContent = 'center';
scrollTopButton.style.cursor = 'pointer';
scrollTopButton.style.boxShadow = '0 4px 10px rgba(0, 0, 0, 0.2)';
scrollTopButton.style.transition = 'all 0.3s ease';
scrollTopButton.style.opacity = '0';  // Initially hidden
scrollTopButton.style.transform = 'translateY(20px)';  // Starting position
document.body.appendChild(scrollTopButton);

// Scroll to top on click
scrollTopButton.addEventListener('click', () => {
    window.scrollTo({
        top: 0,
        behavior: 'smooth'
    });
});

// Show button on scroll
window.addEventListener('scroll', () => {
    if (window.pageYOffset > 200) {
        scrollTopButton.style.opacity = '1';
        scrollTopButton.style.transform = 'translateY(0)';
    } else {
        scrollTopButton.style.opacity = '0';
        scrollTopButton.style.transform = 'translateY(20px)';
    }
});


document.addEventListener("DOMContentLoaded", () => {
    const modal = document.getElementById("modal");
    const modalTitle = document.getElementById("modal-title");
    const modalDescription = document.getElementById("modal-description");
    const closeModal = document.querySelector(".close");

    const groupDetails = {
        "7-9 ani": `
            <p>În această grupă, copiii învață bazele programării, inclusiv logica algoritmică și utilizarea unor platforme simple precum Scratch.</p> 
            <strong>Ce pot învăța:</strong>
            <ul>
                <li>Cum să creeze animații și jocuri interactive</li>
                <li>Bazele gândirii logice și structurale</li>
            </ul>
            <strong>Unde le va fi util:</strong>
            <p>Aceste abilități dezvoltă gândirea creativă și logică, utile în orice domeniu viitor.</p>
        `,
        "10-13 ani": `
            Elevii explorează concepte avansate de programare, cum ar fi crearea de site-uri web și utilizarea limbajelor precum HTML și CSS.
            <br><strong>Ce pot învăța:</strong>
            <ul>
                <li>Cum să creeze pagini web simple</li>
                <li>Introducere în limbajul Python</li>
            </ul>
            <strong>Unde le va fi util:</strong>
            <br>Le oferă o bază solidă pentru cariere tehnologice sau pentru proiecte școlare inovative.
        `,
        "13-15 ani": `
            Elevii lucrează la proiecte reale, inclusiv dezvoltarea aplicațiilor web sau chiar a jocurilor.
            <br><strong>Ce pot învăța:</strong>
            <ul>
                <li>Crearea aplicațiilor interactive</li>
                <li>Introducere în baze de date și logica algoritmică avansată</li>
            </ul>
            <strong>Unde le va fi util:</strong>
            <br>Aceste abilități sunt foarte căutate în lumea tehnologiei moderne și oferă o perspectivă clară asupra oportunităților de carieră.
        `,
        "15-17 ani": `
            Elevii se concentrează pe tehnologii avansate precum Inteligența Artificială, Data Science sau dezvoltarea aplicațiilor mobile.
            <br><strong>Ce pot învăța:</strong>
            <ul>
                <li>Crearea aplicațiilor pentru Android și iOS</li>
                <li>Tehnologii avansate precum Machine Learning</li>
            </ul>
            <strong>Unde le va fi util:</strong>
            <br>Pregătește elevii pentru studii universitare în IT sau pentru o carieră timpurie în industrie.
        `
    };

    document.querySelectorAll(".learn-more").forEach(button => {
        button.addEventListener("click", () => {
            const ageGroup = button.getAttribute("data-age-group");
            modalTitle.textContent = `Detalii pentru grupa de vârstă ${ageGroup}`;
            modalDescription.innerHTML = groupDetails[ageGroup];
            modal.style.display = "flex";
        });
    });

    closeModal.addEventListener("click", () => {
        modal.style.display = "none";
    });

    window.addEventListener("click", (event) => {
        if (event.target === modal) {
            modal.style.display = "none";
        }
    });
});


