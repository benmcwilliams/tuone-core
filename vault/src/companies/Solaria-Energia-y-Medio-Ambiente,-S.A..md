```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Solaria-Energia-y-Medio-Ambiente,-S.A." or company = "Solaria Energia y Medio Ambiente, S.A.")
sort location, dt_announce desc
```
