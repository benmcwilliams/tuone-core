```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Société-du-Taxi-Électrique-Parisien" or company = "Société du Taxi Électrique Parisien")
sort location, dt_announce desc
```
