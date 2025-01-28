```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Réseau-de-Transport-d’Electricité" or company = "Réseau de Transport d’Electricité")
sort location, dt_announce desc
```
