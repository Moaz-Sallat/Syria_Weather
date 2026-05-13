<template>
  <div class="home">
    <div class="overlay"></div>

    <div class="content">
      <h1>لوحة الطقس في سوريا</h1>

      <p>
        خريطة تفاعلية تعرض محافظات سوريا مع بيانات الطقس بشكل مباشر
      </p>

      <RouterLink class="cta" to="/dashboard">دخول إلى لوحة التحكم</RouterLink>

      <div class="cards">
        <div class="card">
          <h3>🗺️ خريطة تفاعلية</h3>
          <p>استعرض محافظات سوريا بسهولة.</p>
        </div>

        <div class="card">
          <h3>🌦️ بيانات الطقس</h3>
          <p>اعرض الحرارة والرطوبة وحالة الجو.</p>
        </div>

        <div class="card">
          <h3>⚡ تحديث سريع</h3>
          <p>واجهة سهلة وسريعة الاستخدام.</p>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.home {
  min-height: 100vh;
  position: relative;
  background: linear-gradient(135deg, #1e88e5, #00acc1);
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  direction: rtl;
}

.overlay {
  position: absolute;
  width: 550px;
  height: 550px;
  background: rgba(255, 255, 255, 0.15);
  border-radius: 50%;
  top: -120px;
  left: -120px;
}

.content {
  position: relative;
  text-align: center;
  color: white;
  max-width: 900px;
  padding: 30px;
}

h1 {
  font-size: 48px;
  margin-bottom: 15px;
}

p {
  font-size: 20px;
  margin-bottom: 25px;
}

.cta {
  display: inline-block;
  background: white;
  color: #1e88e5;
  border: none;
  padding: 14px 35px;
  font-size: 18px;
  font-weight: 700;
  border-radius: 30px;
  cursor: pointer;
  transition: transform 0.3s, background 0.3s;
  text-decoration: none;
}

.cta:hover {
  transform: scale(1.05);
  background: #f1f1f1;
}

.cta:focus-visible {
  outline: 3px solid rgba(255, 255, 255, 0.9);
  outline-offset: 3px;
}

.cards {
  display: flex;
  gap: 20px;
  margin-top: 45px;
  justify-content: center;
  flex-wrap: wrap;
}

.card {
  background: rgba(255, 255, 255, 0.18);
  padding: 20px;
  width: 230px;
  border-radius: 18px;
  backdrop-filter: blur(8px);
  transition: 0.3s;
}

.card:hover {
  transform: translateY(-10px);
  background: rgba(255, 255, 255, 0.28);
}

.card h3 {
  margin-bottom: 10px;
}

.card p {
  font-size: 15px;
  margin: 0;
}
</style>