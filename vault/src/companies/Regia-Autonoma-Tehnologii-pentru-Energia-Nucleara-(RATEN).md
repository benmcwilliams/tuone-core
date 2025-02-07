```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Regia-Autonoma-Tehnologii-pentru-Energia-Nucleara-(RATEN)" or company = "Regia Autonoma Tehnologii pentru Energia Nucleara (RATEN)")
sort location, dt_announce desc
```
