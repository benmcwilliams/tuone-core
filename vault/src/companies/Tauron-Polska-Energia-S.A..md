```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Tauron-Polska-Energia-S.A." or company = "Tauron Polska Energia S.A.")
sort location, dt_announce desc
```
