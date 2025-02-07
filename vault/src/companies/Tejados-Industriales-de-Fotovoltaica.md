```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Tejados-Industriales-de-Fotovoltaica" or company = "Tejados Industriales de Fotovoltaica")
sort location, dt_announce desc
```
