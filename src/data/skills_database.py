"""
Comprehensive Skills Database
Contains salary ranges, curated resources, and market information for all supported skills.
Last Updated: 2025-01-05
"""

SKILLS_DATABASE = {    
    # ===== CLOUD & DEVOPS =====
    "AWS": {
        "category": "Cloud & DevOps",
        "salary_range": "$110,000 - $160,000",
        "salary_min": 110000,
        "salary_max": 160000,
        "market_info": {
            "demand": "Very High",
            "growth_rate": "+30%",
            "open_positions": "60,000+",
            "top_employers": ["Amazon", "Netflix", "Airbnb", "Capital One", "GE", "NASA"],
            "related_roles": ["Cloud Engineer", "Solutions Architect", "DevOps Engineer", "Cloud Consultant"]
        },
        "resources": {
            "beginner": {
                "youtube": ["freeCodeCamp.org", "AWS Online Tech Talks", "Simplilearn"],
                "websites": ["Aws.amazon.com/training", "Aws.amazon.com/getting-started", "Coursera"]
            },
            "intermediate": {
                "youtube": ["Adrian Cantrill", "Stephane Maarek", "A Cloud Guru"],
                "websites": ["Re:Invent.aws", "Udemy", "Linux Academy"]
            },
            "advanced": {
                "youtube": ["AWS re:Invent", "AWS Summits", "AWS This Week"],
                "websites": ["AWS Well-Architected", "AWS Whitepapers", "AWS Architecture Center"]
            }
        }
    },
    # ===== DATA SCIENCE & AI =====
    "Machine Learning": {
        "category": "Data Science & AI",
        "salary_range": "$100,000 - $180,000",
        "salary_min": 100000,
        "salary_max": 180000,
        "market_info": {
            "demand": "Very High",
            "growth_rate": "+35%",
            "open_positions": "50,000+",
            "top_employers": ["Google", "Meta", "Amazon", "Microsoft", "OpenAI", "Tesla"],
            "related_roles": ["ML Engineer", "Data Scientist", "AI Research Scientist", "MLOps Engineer"]
        },
        "resources": {
            "beginner": {
                "youtube": ["3Blue1Brown", "Sentdex", "freeCodeCamp.org"],
                "websites": ["Coursera", "Kaggle", "Datacamp"]
            },
            "intermediate": {
                "youtube": ["DeepLearningAI", "Andrej Karpathy", "StatQuest with Josh Starmer"],
                "websites": ["Fast.ai", "MachineLearningMastery", "TowardsDataScience"]
            },
            "advanced": {
                "youtube": ["Two Minute Papers", "Andrej Karpathy", "DeepLearningAI"],
                "websites": ["ArXiv.org", "Papers with Code", "Distill.pub"]
            }
        }
    },
    
    "Deep Learning": {
        "category": "Data Science & AI",
        "salary_range": "$130,000 - $200,000",
        "salary_min": 130000,
        "salary_max": 200000,
        "market_info": {
            "demand": "Very High",
            "growth_rate": "+40%",
            "open_positions": "35,000+",
            "top_employers": ["OpenAI", "Google DeepMind", "Meta AI", "NVIDIA", "Tesla", "Amazon"],
            "related_roles": ["Deep Learning Engineer", "AI Researcher", "Computer Vision Engineer", "NLP Engineer"]
        },
        "resources": {
            "beginner": {
                "youtube": ["DeepLearningAI", "Sentdex", "3Blue1Brown"],
                "websites": ["Coursera", "Fast.ai", "TensorFlow.org"]
            },
            "intermediate": {
                "youtube": ["Andrej Karpathy", "Siraj Raval", "DeepLearningAI"],
                "websites": ["PyTorch.org", "TowardsDataScience", "Papers with Code"]
            },
            "advanced": {
                "youtube": ["Two Minute Papers", "Yannic Kilcher", "AI Coffee Break"],
                "websites": ["ArXiv.org", "Distill.pub", "OpenAI Research"]
            }
        }
    },
    
    "Data Analysis": {
        "category": "Data Science & AI",
        "salary_range": "$90,000 - $130,000",
        "salary_min": 90000,
        "salary_max": 130000,
        "market_info": {
            "demand": "High",
            "growth_rate": "+25%",
            "open_positions": "80,000+",
            "top_employers": ["Google", "Amazon", "Microsoft", "Meta", "Netflix", "Uber"],
            "related_roles": ["Data Analyst", "Business Analyst", "Data Scientist", "Analytics Engineer"]
        },
        "resources": {
            "beginner": {
                "youtube": ["freeCodeCamp.org", "Data School", "Corey Schafer"],
                "websites": ["Datacamp", "Kaggle", "Mode Analytics"]
            },
            "intermediate": {
                "youtube": ["StatQuest with Josh Starmer", "Brandon Foltz", "Ken Jee"],
                "websites": ["TowardsDataScience", "AnalyticsVidhya", "Tableau Public"]
            },
            "advanced": {
                "youtube": ["StatQuest with Josh Starmer", "Data Science Dojo"],
                "websites": ["KDnuggets", "Analytics Vidhya", "Kaggle Competitions"]
            }
        }
    },
    
    "Natural Language Processing": {
        "category": "Data Science & AI",
        "salary_range": "$100,000 - $150,000",
        "salary_min": 100000,
        "salary_max": 150000,
        "market_info": {
            "demand": "Very High",
            "growth_rate": "+38%",
            "open_positions": "25,000+",
            "top_employers": ["OpenAI", "Google", "Meta", "Amazon", "Microsoft", "Anthropic"],
            "related_roles": ["NLP Engineer", "Computational Linguist", "ML Engineer", "AI Researcher"]
        },
        "resources": {
            "beginner": {
                "youtube": ["Sentdex", "freeCodeCamp.org", "Krish Naik"],
                "websites": ["Coursera", "NLTK.org", "Spacy.io"]
            },
            "intermediate": {
                "youtube": ["DeepLearningAI", "Stanford NLP", "Jay Alammar"],
                "websites": ["HuggingFace.co", "TowardsDataScience", "Papers with Code"]
            },
            "advanced": {
                "youtube": ["Yannic Kilcher", "AI Coffee Break", "Stanford CS224N"],
                "websites": ["ArXiv.org", "ACL Anthology", "OpenAI Research"]
            }
        }
    },
    
    "Computer Vision": {
        "category": "Data Science & AI",
        "salary_range": "$80,000 - $170,000",
        "salary_min": 80000,
        "salary_max": 170000,
        "market_info": {
            "demand": "Very High",
            "growth_rate": "+36%",
            "open_positions": "30,000+",
            "top_employers": ["Tesla", "NVIDIA", "Meta", "Google", "Amazon", "Apple"],
            "related_roles": ["Computer Vision Engineer", "ML Engineer", "Robotics Engineer", "AI Researcher"]
        },
        "resources": {
            "beginner": {
                "youtube": ["freeCodeCamp.org", "Sentdex", "OpenCV"],
                "websites": ["OpenCV.org", "PyImageSearch", "Coursera"]
            },
            "intermediate": {
                "youtube": ["DeepLearningAI", "Two Minute Papers", "First Principles of Computer Vision"],
                "websites": ["PyTorch.org/vision", "TowardsDataScience", "Papers with Code"]
            },
            "advanced": {
                "youtube": ["Yannic Kilcher", "AI Coffee Break", "CVPR Talks"],
                "websites": ["ArXiv.org", "CVPR Conference", "ECCV Conference"]
            }
        }
    },
    
    "Data Engineering": {
        "category": "Data Science & AI",
        "salary_range": "$120,000 - $180,000",
        "salary_min": 120000,
        "salary_max": 180000,
        "market_info": {
            "demand": "Very High",
            "growth_rate": "+30%",
            "open_positions": "45,000+",
            "top_employers": ["Amazon", "Google", "Microsoft", "Meta", "Uber", "Airbnb"],
            "related_roles": ["Data Engineer", "Analytics Engineer", "ETL Developer", "Big Data Engineer"]
        },
        "resources": {
            "beginner": {
                "youtube": ["freeCodeCamp.org", "Corey Schafer", "Tech With Tim"],
                "websites": ["Datacamp", "Coursera", "Mode Analytics"]
            },
            "intermediate": {
                "youtube": ["Databricks", "Apache Spark", "Seattle Data Guy"],
                "websites": ["Databricks.com", "Apache.org/Spark", "TowardsDataScience"]
            },
            "advanced": {
                "youtube": ["Data Engineering Podcast", "Advancing Analytics"],
                "websites": ["Databricks University", "Confluent.io", "DataEngineeringPodcast"]
            }
        }
    },
    
    "Big Data": {
        "category": "Data Science & AI",
        "salary_range": "$110,000 - $160,000",
        "salary_min": 110000,
        "salary_max": 160000,
        "market_info": {
            "demand": "High",
            "growth_rate": "+28%",
            "open_positions": "40,000+",
            "top_employers": ["Amazon", "Google", "Microsoft", "IBM", "Oracle", "Cloudera"],
            "related_roles": ["Big Data Engineer", "Data Architect", "Hadoop Developer", "Data Platform Engineer"]
        },
        "resources": {
            "beginner": {
                "youtube": ["Simplilearn", "Edureka", "freeCodeCamp.org"],
                "websites": ["Hadoop.apache.org", "Cloudera.com", "Coursera"]
            },
            "intermediate": {
                "youtube": ["Hadoop Illuminated", "Databricks", "Apache Spark"],
                "websites": ["Apache.org/Spark", "Databricks.com", "KDnuggets"]
            },
            "advanced": {
                "youtube": ["Data Engineering Podcast", "Confluent"],
                "websites": ["Confluent.io", "Apache Kafka", "BigDataUniversity"]
            }
        }
    },
    
    "AI Ethics": {
        "category": "Data Science & AI",
        "salary_range": "$120,000 - $170,000",
        "salary_min": 120000,
        "salary_max": 170000,
        "market_info": {
            "demand": "Growing",
            "growth_rate": "+45%",
            "open_positions": "5,000+",
            "top_employers": ["OpenAI", "Google", "Meta", "Microsoft", "Anthropic", "Partnership on AI"],
            "related_roles": ["AI Ethics Researcher", "Responsible AI Lead", "AI Policy Analyst", "ML Fairness Engineer"]
        },
        "resources": {
            "beginner": {
                "youtube": ["TED-Ed", "Computerphile", "CrashCourse"],
                "websites": ["AIethicsguidelines.global", "Coursera", "Ethics.ai"]
            },
            "intermediate": {
                "youtube": ["DeepLearningAI", "Stanford HAI", "Montreal AI Ethics Institute"],
                "websites": ["Futureoflife.org", "AIindex.stanford.edu", "Partnership on AI"]
            },
            "advanced": {
                "youtube": ["Timnit Gebru", "Kate Crawford", "Joy Buolamwini"],
                "websites": ["FAccT Conference", "AIES Conference", "ArXiv.org"]
            }
        }
    },
    
    # ===== WEB DEVELOPMENT =====
    "Frontend (React, Vue, Angular)": {
        "category": "Web Development",
        "salary_range": "$100,000 - $140,000",
        "salary_min": 100000,
        "salary_max": 140000,
        "market_info": {
            "demand": "Very High",
            "growth_rate": "+22%",
            "open_positions": "100,000+",
            "top_employers": ["Meta", "Google", "Amazon", "Netflix", "Airbnb", "Uber"],
            "related_roles": ["Frontend Developer", "UI Engineer", "React Developer", "Web Developer"]
        },
        "resources": {
            "beginner": {
                "youtube": ["Traversy Media", "freeCodeCamp.org", "The Net Ninja"],
                "websites": ["Reactjs.org", "MDN Web Docs", "FreeCodeCamp"]
            },
            "intermediate": {
                "youtube": ["Academind", "Fireship", "Web Dev Simplified"],
                "websites": ["Vuejs.org", "Angular.io", "FrontendMasters"]
            },
            "advanced": {
                "youtube": ["Jack Herrington", "Theo - t3.gg", "UI.dev"],
                "websites": ["React Advanced", "Patterns.dev", "Web.dev"]
            }
        }
    },
    
    "Backend (Node.js, Django, Flask)": {
        "category": "Web Development",
        "salary_range": "$110,000 - $150,000",
        "salary_min": 110000,
        "salary_max": 150000,
        "market_info": {
            "demand": "Very High",
            "growth_rate": "+25%",
            "open_positions": "90,000+",
            "top_employers": ["Amazon", "Google", "Microsoft", "Meta", "Netflix", "Uber"],
            "related_roles": ["Backend Developer", "API Developer", "Software Engineer", "Full Stack Developer"]
        },
        "resources": {
            "beginner": {
                "youtube": ["Traversy Media", "freeCodeCamp.org", "Corey Schafer"],
                "websites": ["Nodejs.org", "Djangoproject.com", "Flask.palletsprojects.com"]
            },
            "intermediate": {
                "youtube": ["Programming with Mosh", "The Net Ninja", "Tech With Tim"],
                "websites": ["Expressjs.com", "FastAPI.tiangolo.com", "RealPython"]
            },
            "advanced": {
                "youtube": ["Hussein Nasser", "CodeOpinion", "ArjanCodes"],
                "websites": ["System Design Primer", "Microservices.io", "Martin Fowler"]
            }
        }
    },
    
    "Full Stack": {
        "category": "Web Development",
        "salary_range": "$110,000 - $170,000",
        "salary_min": 110000,
        "salary_max": 170000,
        "market_info": {
            "demand": "Very High",
            "growth_rate": "+27%",
            "open_positions": "120,000+",
            "top_employers": ["Amazon", "Google", "Meta", "Microsoft", "Shopify", "Stripe"],
            "related_roles": ["Full Stack Developer", "Software Engineer", "Web Developer", "Application Developer"]
        },
        "resources": {
            "beginner": {
                "youtube": ["freeCodeCamp.org", "Traversy Media", "The Net Ninja"],
                "websites": ["Fullstackopen.com", "FreeCodeCamp", "Codecademy"]
            },
            "intermediate": {
                "youtube": ["Academind", "Web Dev Simplified", "Fireship"],
                "websites": ["Udemy", "Coursera", "Dev.to"]
            },
            "advanced": {
                "youtube": ["Theo - t3.gg", "Jack Herrington", "Hussein Nasser"],
                "websites": ["System Design", "Microservices Patterns", "Web.dev"]
            }
        }
    },
    
    "JavaScript": {
        "category": "Web Development",
        "salary_range": "$100,000 - $140,000",
        "salary_min": 100000,
        "salary_max": 140000,
        "market_info": {
            "demand": "Very High",
            "growth_rate": "+20%",
            "open_positions": "150,000+",
            "top_employers": ["Google", "Meta", "Amazon", "Microsoft", "Netflix", "Airbnb"],
            "related_roles": ["JavaScript Developer", "Frontend Developer", "Full Stack Developer", "Web Developer"]
        },
        "resources": {
            "beginner": {
                "youtube": ["Traversy Media", "freeCodeCamp.org", "Programming with Mosh"],
                "websites": ["Javascript.info", "MDN Web Docs", "FreeCodeCamp"]
            },
            "intermediate": {
                "youtube": ["The Net Ninja", "Web Dev Simplified", "Fireship"],
                "websites": ["Eloquentjavascript.net", "JavaScript30", "Frontend Masters"]
            },
            "advanced": {
                "youtube": ["Fun Fun Function", "MPJ", "Theo - t3.gg"],
                "websites": ["You Don't Know JS", "JavaScript Weekly", "TC39 Proposals"]
            }
        }
    },
    
    "TypeScript": {
        "category": "Web Development",
        "salary_range": "$110,000 - $150,000",
        "salary_min": 110000,
        "salary_max": 150000,
        "market_info": {
            "demand": "Very High",
            "growth_rate": "+35%",
            "open_positions": "80,000+",
            "top_employers": ["Microsoft", "Google", "Meta", "Amazon", "Airbnb", "Stripe"],
            "related_roles": ["TypeScript Developer", "Frontend Engineer", "Full Stack Developer", "Software Engineer"]
        },
        "resources": {
            "beginner": {
                "youtube": ["Traversy Media", "freeCodeCamp.org", "The Net Ninja"],
                "websites": ["Typescriptlang.org", "TypeScript Handbook", "Execute Program"]
            },
            "intermediate": {
                "youtube": ["Academind", "Matt Pocock", "Jack Herrington"],
                "websites": ["Basarat.gitbook.io/typescript", "Total TypeScript", "Frontend Masters"]
            },
            "advanced": {
                "youtube": ["Matt Pocock", "Theo - t3.gg", "Jack Herrington"],
                "websites": ["Type Challenges", "Advanced TypeScript", "TypeScript Deep Dive"]
            }
        }
    },
    
    "Web Performance": {
        "category": "Web Development",
        "salary_range": "$110,000 - $150,000",
        "salary_min": 110000,
        "salary_max": 150000,
        "market_info": {
            "demand": "High",
            "growth_rate": "+30%",
            "open_positions": "15,000+",
            "top_employers": ["Google", "Meta", "Amazon", "Netflix", "Cloudflare", "Vercel"],
            "related_roles": ["Performance Engineer", "Frontend Engineer", "Web Developer", "Site Reliability Engineer"]
        },
        "resources": {
            "beginner": {
                "youtube": ["Google Chrome Developers", "Web Dev Simplified", "Fireship"],
                "websites": ["Web.dev", "MDN Performance", "PageSpeed Insights"]
            },
            "intermediate": {
                "youtube": ["Harry Roberts", "Addy Osmani", "Paul Irish"],
                "websites": ["Developers.google.com/web", "Smashingmagazine.com", "Perf.rocks"]
            },
            "advanced": {
                "youtube": ["Chrome Dev Summit", "Performance.now()"],
                "websites": ["WebPageTest", "Lighthouse CI", "Web Vitals"]
            }
        }
    },
    
    "Web Security": {
        "category": "Web Development",
        "salary_range": "$110,000 - $150,000",
        "salary_min": 110000,
        "salary_max": 150000,
        "market_info": {
            "demand": "Very High",
            "growth_rate": "+32%",
            "open_positions": "25,000+",
            "top_employers": ["Google", "Meta", "Amazon", "Microsoft", "Cloudflare", "Auth0"],
            "related_roles": ["Security Engineer", "Application Security Engineer", "Web Developer", "DevSecOps Engineer"]
        },
        "resources": {
            "beginner": {
                "youtube": ["freeCodeCamp.org", "Traversy Media", "OWASP"],
                "websites": ["Owasp.org", "Web.dev/security", "MDN Security"]
            },
            "intermediate": {
                "youtube": ["LiveOverflow", "The Cyber Mentor", "PwnFunction"],
                "websites": ["Portswigger.net", "HackerOne", "BugBountyHunter"]
            },
            "advanced": {
                "youtube": ["LiveOverflow", "IppSec", "John Hammond"],
                "websites": ["OWASP Top 10", "Web Security Academy", "HackerOne Reports"]
            }
        }
    },
    
    "Progressive Web Apps": {
        "category": "Web Development",
        "salary_range": "$110,000 - $150,000",
        "salary_min": 110000,
        "salary_max": 150000,
        "market_info": {
            "demand": "Growing",
            "growth_rate": "+28%",
            "open_positions": "20,000+",
            "top_employers": ["Google", "Microsoft", "Twitter", "Starbucks", "Uber", "Pinterest"],
            "related_roles": ["PWA Developer", "Frontend Developer", "Mobile Web Developer", "Web Developer"]
        },
        "resources": {
            "beginner": {
                "youtube": ["Google Chrome Developers", "Traversy Media", "freeCodeCamp.org"],
                "websites": ["Web.dev/progressive-web-apps", "PWA Builder", "MDN PWA"]
            },
            "intermediate": {
                "youtube": ["Academind", "Maximilian Schwarzmüller", "Fireship"],
                "websites": ["Developers.google.com/web/pwa", "Workboxjs.org", "PWA Stats"]
            },
            "advanced": {
                "youtube": ["Chrome Dev Summit", "Google I/O"],
                "websites": ["Service Worker Cookbook", "PWA Directory", "Web Capabilities"]
            }
        }
    },
    
    # ===== MOBILE DEVELOPMENT =====
    "iOS Development": {
        "category": "Mobile Development",
        "salary_range": "$120,000 - $160,000",
        "salary_min": 120000,
        "salary_max": 160000,
        "market_info": {
            "demand": "High",
            "growth_rate": "+18%",
            "open_positions": "40,000+",
            "top_employers": ["Apple", "Meta", "Amazon", "Uber", "Airbnb", "Netflix"],
            "related_roles": ["iOS Engineer", "Swift Developer", "Mobile Developer", "App Developer"]
        },
        "resources": {
            "beginner": {
                "youtube": ["CodeWithChris", "Sean Allen", "iOS Academy"],
                "websites": ["Developer.apple.com", "Hackingwithswift.com", "Raywenderlich.com"]
            },
            "intermediate": {
                "youtube": ["Lets Build That App", "Kavsoft", "SwiftUI Lab"],
                "websites": ["Swift.org", "Apple Developer Tutorials", "Udemy"]
            },
            "advanced": {
                "youtube": ["WWDC Videos", "Point-Free", "Swift by Sundell"],
                "websites": ["Swift Forums", "NSHipster", "objc.io"]
            }
        }
    },
    
    "Android Development": {
        "category": "Mobile Development",
        "salary_range": "$100,000 - $140,000",
        "salary_min": 100000,
        "salary_max": 140000,
        "market_info": {
            "demand": "High",
            "growth_rate": "+20%",
            "open_positions": "50,000+",
            "top_employers": ["Google", "Meta", "Amazon", "Uber", "Netflix", "Spotify"],
            "related_roles": ["Android Engineer", "Kotlin Developer", "Mobile Developer", "App Developer"]
        },
        "resources": {
            "beginner": {
                "youtube": ["Philipp Lackner", "freeCodeCamp.org", "Android Developers"],
                "websites": ["Developer.android.com", "Kotlinlang.org", "Udacity"]
            },
            "intermediate": {
                "youtube": ["Coding in Flow", "Reso Coder", "Stevdza-San"],
                "websites": ["Raywenderlich.com", "Vogella", "Android Weekly"]
            },
            "advanced": {
                "youtube": ["Android Developers", "Philipp Lackner Advanced", "Coding with Mitch"],
                "websites": ["Android Dev Summit", "ProAndroidDev", "Android Arsenal"]
            }
        }
    },
    
    "React Native": {
        "category": "Mobile Development",
        "salary_range": "$100,000 - $150,000",
        "salary_min": 100000,
        "salary_max": 150000,
        "market_info": {
            "demand": "High",
            "growth_rate": "+25%",
            "open_positions": "35,000+",
            "top_employers": ["Meta", "Microsoft", "Tesla", "Shopify", "Discord", "Coinbase"],
            "related_roles": ["React Native Developer", "Mobile Developer", "Cross-Platform Developer", "JavaScript Developer"]
        },
        "resources": {
            "beginner": {
                "youtube": ["freeCodeCamp.org", "The Net Ninja", "Programming with Mosh"],
                "websites": ["Reactnative.dev", "Expo.dev", "React Native School"]
            },
            "intermediate": {
                "youtube": ["Academind", "Maximilian Schwarzmüller", "Not Just Dev"],
                "websites": ["Udemy", "Coursera", "React Native Directory"]
            },
            "advanced": {
                "youtube": ["William Candillon", "Catalin Miron", "Infinite Red"],
                "websites": ["React Native EU", "Chain React", "React Native Radio"]
            }
        }
    },
    
    "Flutter": {
        "category": "Mobile Development",
        "salary_range": "$100,000 - $140,000",
        "salary_min": 100000,
        "salary_max": 140000,
        "market_info": {
            "demand": "Growing",
            "growth_rate": "+30%",
            "open_positions": "30,000+",
            "top_employers": ["Google", "Alibaba", "BMW", "eBay", "Groupon", "Philips"],
            "related_roles": ["Flutter Developer", "Mobile Developer", "Dart Developer", "Cross-Platform Developer"]
        },
        "resources": {
            "beginner": {
                "youtube": ["The Net Ninja", "freeCodeCamp.org", "Flutter"],
                "websites": ["Flutter.dev", "Dart.dev", "Flutter Codelabs"]
            },
            "intermediate": {
                "youtube": ["Reso Coder", "Academind", "Robert Brunhage"],
                "websites": ["Udemy", "Coursera", "Flutter Awesome"]
            },
            "advanced": {
                "youtube": ["Flutter Europe", "Filledstacks", "Reso Coder Advanced"],
                "websites": ["Flutter Engage", "DartPad", "Pub.dev"]
            }
        }
    },
    
    "Mobile UI/UX": {
        "category": "Mobile Development",
        "salary_range": "$90,000 - $130,000",
        "salary_min": 90000,
        "salary_max": 130000,
        "market_info": {
            "demand": "High",
            "growth_rate": "+22%",
            "open_positions": "25,000+",
            "top_employers": ["Apple", "Google", "Meta", "Airbnb", "Uber", "Netflix"],
            "related_roles": ["Mobile UI Designer", "UX Designer", "Product Designer", "Interaction Designer"]
        },
        "resources": {
            "beginner": {
                "youtube": ["DesignCourse", "Flux Academy", "Jesse Showalter"],
                "websites": ["Material.io", "Humaninterface.apple.com", "Uxdesign.cc"]
            },
            "intermediate": {
                "youtube": ["ChunBuns", "Mizko", "Malewicz"],
                "websites": ["Interaction-design.org", "Adobe.com/xd", "Figma.com"]
            },
            "advanced": {
                "youtube": ["Config by Figma", "Apple Design Resources"],
                "websites": ["WWDC Design Sessions", "Material Design Awards", "Mobbin"]
            }
        }
    },
    
    "Cross-Platform": {
        "category": "Mobile Development",
        "salary_range": "$100,000 - $140,000",
        "salary_min": 100000,
        "salary_max": 140000,
        "market_info": {
            "demand": "High",
            "growth_rate": "+28%",
            "open_positions": "40,000+",
            "top_employers": ["Microsoft", "Google", "Meta", "Shopify", "Adobe", "SAP"],
            "related_roles": ["Cross-Platform Developer", "Mobile Developer", "Hybrid App Developer", "Multi-Platform Engineer"]
        },
        "resources": {
            "beginner": {
                "youtube": ["freeCodeCamp.org", "Academind", "The Net Ninja"],
                "websites": ["Reactnative.dev", "Flutter.dev", "Ionicframework.com"]
            },
            "intermediate": {
                "youtube": ["Simon Grimm", "Fireship", "Traversy Media"],
                "websites": ["Xamarin.com", "Capacitorjs.com", "Udemy"]
            },
            "advanced": {
                "youtube": ["React Native EU", "Flutter Engage", "Ionic Conf"],
                "websites": ["Native Script", "Kotlin Multiplatform", "Tauri"]
            }
        }
    },
    
    "Mobile Games": {
        "category": "Mobile Development",
        "salary_range": "$90,000 - $140,000",
        "salary_min": 90000,
        "salary_max": 140000,
        "market_info": {
            "demand": "Moderate",
            "growth_rate": "+15%",
            "open_positions": "20,000+",
            "top_employers": ["King", "Supercell", "Rovio", "Zynga", "Electronic Arts", "Activision"],
            "related_roles": ["Mobile Game Developer", "Unity Developer", "Game Programmer", "Gameplay Engineer"]
        },
        "resources": {
            "beginner": {
                "youtube": ["Brackeys", "Blackthornprod", "Unity"],
                "websites": ["Unity.com/learn", "Gamedev.tv", "Itch.io"]
            },
            "intermediate": {
                "youtube": ["Code Monkey", "Jonas Tyroller", "Dani"],
                "websites": ["Udemy", "Coursera", "Gamedev.net"]
            },
            "advanced": {
                "youtube": ["GDC", "Unite Conference", "Game Maker's Toolkit"],
                "websites": ["Gamasutra", "Unity Asset Store", "Unreal Marketplace"]
            }
        }
    },
    
    "Mobile Security": {
        "category": "Mobile Development",
        "salary_range": "$100,000 - $150,000",
        "salary_min": 100000,
        "salary_max": 150000,
        "market_info": {
            "demand": "High",
            "growth_rate": "+35%",
            "open_positions": "15,000+",
            "top_employers": ["Apple", "Google", "Meta", "Amazon", "Microsoft", "Zimperium"],
            "related_roles": ["Mobile Security Engineer", "Application Security Engineer", "Security Researcher", "Penetration Tester"]
        },
        "resources": {
            "beginner": {
                "youtube": ["The Cyber Mentor", "NetworkChuck", "freeCodeCamp.org"],
                "websites": ["Owasp.org/mobile", "Developer.android.com/security", "Developer.apple.com/security"]
            },
            "intermediate": {
                "youtube": ["LiveOverflow", "John Hammond", "David Bombal"],
                "websites": ["HackerOne", "Bugcrowd", "Mobile Security Testing Guide"]
            },
            "advanced": {
                "youtube": ["Black Hat", "DEF CON", "OWASP Mobile"],
                "websites": ["OWASP MSTG", "Mobile Security Framework", "Frida"]
            }
        }
    },
    
    # ===== EMERGING AI ROLES 2025 =====
    "Prompt Engineering": {
        "category": "Emerging AI Roles",
        "salary_range": "$140,000 - $220,000",
        "salary_min": 140000,
        "salary_max": 220000,
        "market_info": {
            "demand": "Very High",
            "growth_rate": "+60%",
            "open_positions": "12,000+",
            "top_employers": ["OpenAI", "Anthropic", "Google", "Microsoft", "Meta", "Startups"],
            "related_roles": ["Prompt Engineer", "AI Product Manager", "LLM Specialist", "Conversational AI Designer"]
        },
        "description": "A specialist who crafts precise inputs (prompts) for generative AI models to optimize outputs, bridging human intent and AI capabilities.",
        "key_responsibilities": [
            "Designing and testing prompts for optimal AI outputs",
            "Iterating on AI responses for accuracy and relevance",
            "Collaborating with developers to refine models",
            "Training teams on effective prompting techniques",
            "A/B testing different prompt strategies"
        ],
        "resources": {
            "beginner": {
                "youtube": ["OpenAI", "AI Explained", "Matt Wolfe"],
                "websites": ["Learn Prompting", "PromptingGuide.ai", "OpenAI Cookbook"]
            },
            "intermediate": {
                "youtube": ["DeepLearningAI", "Prompt Engineering Guide", "AI Jason"],
                "websites": ["Anthropic Docs", "LangChain Docs", "PromptBase"]
            },
            "advanced": {
                "youtube": ["Andrej Karpathy", "Yannic Kilcher", "AI Coffee Break"],
                "websites": ["ArXiv.org", "Papers with Code", "HuggingFace Research"]
            }
        }
    },
    
    "AI Ethics & Governance": {
        "category": "Emerging AI Roles",
        "salary_range": "$150,000 - $230,000",
        "salary_min": 150000,
        "salary_max": 230000,
        "market_info": {
            "demand": "Very High",
            "growth_rate": "+55%",
            "open_positions": "8,000+",
            "top_employers": ["OpenAI", "Google", "Meta", "Microsoft", "Anthropic", "Partnership on AI"],
            "related_roles": ["AI Ethics Officer", "Responsible AI Lead", "AI Policy Analyst", "AI Governance Specialist"]
        },
        "description": "An expert focused on ensuring AI systems are fair, transparent, and unbiased, addressing regulatory and societal concerns in AI deployment.",
        "key_responsibilities": [
            "Auditing AI systems for bias and fairness",
            "Developing ethical guidelines and frameworks",
            "Conducting AI impact assessments",
            "Advising on compliance with AI regulations (EU AI Act, etc.)",
            "Stakeholder communication on AI ethics"
        ],
        "resources": {
            "beginner": {
                "youtube": ["TED-Ed", "Computerphile", "CrashCourse AI Ethics"],
                "websites": ["AI Ethics Guidelines", "Ethics.ai", "Partnership on AI"]
            },
            "intermediate": {
                "youtube": ["Stanford HAI", "Montreal AI Ethics Institute", "DeepLearningAI"],
                "websites": ["Futureoflife.org", "AI Index Stanford", "FAccT Conference"]
            },
            "advanced": {
                "youtube": ["Timnit Gebru", "Kate Crawford", "Joy Buolamwini"],
                "websites": ["FAccT Conference", "AIES Conference", "ArXiv AI Ethics"]
            }
        }
    },
    
    "AI Auditing": {
        "category": "Emerging AI Roles",
        "salary_range": "$130,000 - $200,000",
        "salary_min": 130000,
        "salary_max": 200000,
        "market_info": {
            "demand": "High",
            "growth_rate": "+50%",
            "open_positions": "6,000+",
            "top_employers": ["Deloitte", "PwC", "KPMG", "EY", "Tech Companies", "Financial Institutions"],
            "related_roles": ["AI Auditor", "ML Compliance Specialist", "AI Risk Analyst", "Algorithm Auditor"]
        },
        "description": "A role involving the inspection of AI systems for accuracy, security, and explainability, similar to financial auditing but for algorithms.",
        "key_responsibilities": [
            "Performing AI risk assessments",
            "Documenting AI decision processes",
            "Verifying model performance and accuracy",
            "Reporting on vulnerabilities or errors",
            "Ensuring regulatory compliance"
        ],
        "resources": {
            "beginner": {
                "youtube": ["AI Auditing Basics", "Computerphile", "freeCodeCamp.org"],
                "websites": ["ISO AI Standards", "NIST AI Framework", "Coursera"]
            },
            "intermediate": {
                "youtube": ["DeepLearningAI", "Stanford AI Audit", "AI Explained"],
                "websites": ["SHAP Documentation", "LIME Tutorials", "TowardsDataScience"]
            },
            "advanced": {
                "youtube": ["NeurIPS Talks", "ICML Tutorials", "AI Audit Research"],
                "websites": ["ArXiv.org", "AI Audit Tools", "Explainable AI Research"]
            }
        }
    },
    
    "Generative AI Engineering": {
        "category": "Emerging AI Roles",
        "salary_range": "$160,000 - $250,000",
        "salary_min": 160000,
        "salary_max": 250000,
        "market_info": {
            "demand": "Very High",
            "growth_rate": "+70%",
            "open_positions": "15,000+",
            "top_employers": ["OpenAI", "Stability AI", "Midjourney", "Google", "Meta", "Adobe"],
            "related_roles": ["Generative AI Engineer", "GenAI Developer", "Diffusion Model Specialist", "Creative AI Engineer"]
        },
        "description": "A developer specializing in building and deploying generative models for content creation (text, images, video), fueled by tools like DALL-E and Stable Diffusion.",
        "key_responsibilities": [
            "Integrating generative AI into applications",
            "Fine-tuning models for specific use cases",
            "Optimizing for scalability and performance",
            "Ensuring output quality and safety",
            "Building APIs for generative models"
        ],
        "resources": {
            "beginner": {
                "youtube": ["Sentdex", "freeCodeCamp.org", "AI Explained"],
                "websites": ["HuggingFace.co", "Stability AI Docs", "OpenAI Platform"]
            },
            "intermediate": {
                "youtube": ["DeepLearningAI", "Andrej Karpathy", "Two Minute Papers"],
                "websites": ["PyTorch.org", "TensorFlow.org", "Papers with Code"]
            },
            "advanced": {
                "youtube": ["Yannic Kilcher", "AI Coffee Break", "CVPR Talks"],
                "websites": ["ArXiv.org", "Distill.pub", "NeurIPS Papers"]
            }
        }
    },
    
    "Human-AI Collaboration": {
        "category": "Emerging AI Roles",
        "salary_range": "$120,000 - $190,000",
        "salary_min": 120000,
        "salary_max": 190000,
        "market_info": {
            "demand": "High",
            "growth_rate": "+45%",
            "open_positions": "7,000+",
            "top_employers": ["Microsoft", "Google", "Salesforce", "Adobe", "Notion", "Figma"],
            "related_roles": ["Human-AI Collaboration Specialist", "AI UX Designer", "Augmented Intelligence Designer", "AI Product Designer"]
        },
        "description": "A professional designing workflows where humans and AI augment each other, focusing on productivity tools and interface optimization.",
        "key_responsibilities": [
            "Creating collaborative AI interfaces",
            "Training users on AI tools",
            "Measuring human-AI performance metrics",
            "Iterating on feedback loops",
            "Designing AI-augmented workflows"
        ],
        "resources": {
            "beginner": {
                "youtube": ["DesignCourse", "Flux Academy", "Google Design"],
                "websites": ["Interaction-design.org", "Nielsen Norman Group", "UX Collective"]
            },
            "intermediate": {
                "youtube": ["Adobe MAX", "Figma Config", "Microsoft Design"],
                "websites": ["Human-AI Interaction", "ACM CHI", "UX Research Methods"]
            },
            "advanced": {
                "youtube": ["CHI Conference", "CSCW Talks", "HCI Research"],
                "websites": ["ArXiv HCI", "ACM Digital Library", "Human-AI Research"]
            }
        }
    },
    
    "AI Agent Architecture": {
        "category": "Emerging AI Roles",
        "salary_range": "$170,000 - $260,000",
        "salary_min": 170000,
        "salary_max": 260000,
        "market_info": {
            "demand": "Very High",
            "growth_rate": "+65%",
            "open_positions": "10,000+",
            "top_employers": ["OpenAI", "Anthropic", "Google DeepMind", "Salesforce", "Microsoft", "Startups"],
            "related_roles": ["AI Agent Architect", "Agentic AI Engineer", "Multi-Agent Systems Developer", "Autonomous AI Engineer"]
        },
        "description": "An engineer who designs autonomous AI agents capable of multi-step tasks (planning, decision-making), rising with agentic AI advancements like Salesforce's Agentforce.",
        "key_responsibilities": [
            "Architecting agent frameworks and systems",
            "Handling multi-agent coordination",
            "Ensuring reliability and error-handling",
            "Scaling for enterprise use",
            "Implementing ethical AI safeguards"
        ],
        "resources": {
            "beginner": {
                "youtube": ["DeepLearningAI", "Sentdex", "AI Explained"],
                "websites": ["LangChain Docs", "AutoGPT", "AgentGPT"]
            },
            "intermediate": {
                "youtube": ["Andrej Karpathy", "Two Minute Papers", "AI Agent Tutorials"],
                "websites": ["LangGraph", "CrewAI", "Multi-Agent Systems"]
            },
            "advanced": {
                "youtube": ["Yannic Kilcher", "AI Coffee Break", "NeurIPS Talks"],
                "websites": ["ArXiv.org", "Reinforcement Learning", "Agent Research Papers"]
            }
        }
    },
}


def get_skill_info(skill_name: str, expertise_level: str = "intermediate") -> dict:
    """
    Get skill information including salary and resources filtered by expertise level.
    
    Args:
        skill_name: Name of the skill (case-insensitive)
        expertise_level: User's expertise level (beginner, intermediate, advanced)
    
    Returns:
        Dictionary with skill information including filtered resources
    """
    # Normalize skill name
    skill_key = None
    for key in SKILLS_DATABASE.keys():
        if key.lower() == skill_name.lower():
            skill_key = key
            break
    
    if not skill_key:
        # Return default data if skill not found
        return {
            "salary_range": "$80,000 - $150,000",
            "market_info": {
                "demand": "Moderate",
                "growth_rate": "+20%",
                "open_positions": "10,000+",
                "top_employers": ["Tech Companies", "Startups", "Enterprises"],
                "related_roles": ["Software Engineer", "Developer", "Technical Specialist"]
            },
            "resources": {
                "youtube": ["freeCodeCamp.org", "Traversy Media", "The Net Ninja"],
                "websites": ["Coursera", "Udemy", "FreeCodeCamp"]
            }
        }
    
    skill_data = SKILLS_DATABASE[skill_key].copy()
    
    # Filter resources by expertise level
    expertise_level = expertise_level.lower()
    if expertise_level not in ["beginner", "intermediate", "advanced"]:
        expertise_level = "intermediate"
    
    if "resources" in skill_data and expertise_level in skill_data["resources"]:
        # Replace full resources dict with just the relevant level
        skill_data["resources"] = skill_data["resources"][expertise_level]
    elif "resources" in skill_data:
        # Fallback to intermediate if level not found
        skill_data["resources"] = skill_data["resources"].get("intermediate", {
            "youtube": ["freeCodeCamp.org", "Traversy Media"],
            "websites": ["Coursera", "Udemy"]
        })
    
    return skill_data


def get_all_categories() -> list:
    """Get list of all unique categories."""
    categories = set()
    for skill_data in SKILLS_DATABASE.values():
        categories.add(skill_data["category"])
    return sorted(list(categories))


def get_skills_by_category(category: str) -> list:
    """Get all skills in a specific category."""
    skills = []
    for skill_name, skill_data in SKILLS_DATABASE.items():
        if skill_data["category"] == category:
            skills.append(skill_name)
    return sorted(skills)
