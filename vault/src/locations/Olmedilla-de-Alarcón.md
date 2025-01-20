```dataview
table company, tech, component, status, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and location = "Olmedilla de Alarcón"
sort company, dt_announce desc
```
