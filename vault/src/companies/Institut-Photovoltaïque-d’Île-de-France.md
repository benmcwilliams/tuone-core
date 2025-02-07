```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Institut-Photovoltaïque-d’Île-de-France" or company = "Institut Photovoltaïque d’Île de France")
sort location, dt_announce desc
```
