```dataview
table company, tech, component, status, capacity, investment_value, dt_announce
from "phases"
where reject-phase = false and location = "Ambite, Olmeda de las Fuentes, Corpa, Nuevo Baztán, Pezuela de las Torres and Valverde de Alcalá"
sort company, dt_announce desc
```
